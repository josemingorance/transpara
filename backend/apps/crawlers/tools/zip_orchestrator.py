"""
ZIP Orchestrator for PLACSP data processing.

Manages the processing of multiple ZIP files containing PLACSP data.
Ensures proper chronological ordering and handles the syndication
chain correctly according to the OpenPLACSP manual.
"""
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from io import BytesIO
from zipfile import ZipFile

import requests


@dataclass
class PlacspZipInfo:
    """Information about a PLACSP ZIP file."""

    filename: str
    url: Optional[str] = None
    date: Optional[datetime] = None  # Extracted from filename
    syndication_id: Optional[str] = None  # e.g., "643"
    base_atom_filename: Optional[str] = None  # e.g., "licitacionesPerfilesContratanteCompleto3.atom"

    def __lt__(self, other: "PlacspZipInfo") -> bool:
        """Compare by date for sorting."""
        if not self.date or not other.date:
            return self.filename < other.filename
        return self.date < other.date


class PlacspZipDateExtractor:
    """
    Extract date information from PLACSP ZIP filenames.

    PLACSP ZIP files follow patterns like:
    - licitacionesPerfilesContratanteCompleto3_202101.zip (YYYYMM format)
    - licitacionesPerfilesContratanteCompleto3_2021.zip (YYYY format)
    """

    # Pattern for YYYYMM (e.g., 202101 for January 2021)
    PATTERN_YYYYMM = re.compile(r"(\d{4})(\d{2})")

    # Pattern for YYYY (e.g., 2021)
    PATTERN_YYYY = re.compile(r"_(\d{4})(?:\.zip|\.ZIP)")

    @classmethod
    def extract_date(cls, filename: str) -> Optional[datetime]:
        """
        Extract date from PLACSP ZIP filename.

        Args:
            filename: ZIP filename

        Returns:
            datetime object or None if date cannot be extracted
        """
        # Look for YYYYMM pattern
        match = cls.PATTERN_YYYYMM.search(filename)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                if 1 <= month <= 12:
                    return datetime(year, month, 1)
            except (ValueError, IndexError):
                pass

        # Fall back to YYYY pattern
        match = cls.PATTERN_YYYY.search(filename)
        if match:
            try:
                year = int(match.group(1))
                return datetime(year, 1, 1)
            except ValueError:
                pass

        return None

    @classmethod
    def extract_syndication_id(cls, filename: str) -> Optional[str]:
        """
        Extract syndication ID from filename.

        Syndication IDs are typically found at the end of the base name
        (before the date), e.g., "643" in "licitacionesPerfilesContratanteCompleto3_202101.zip"

        Args:
            filename: ZIP filename

        Returns:
            Syndication ID or None
        """
        # Look for numbers in specific patterns
        match = re.search(r"Completo(\d+)", filename)
        if match:
            return match.group(1)
        return None


class ZipOrchestrator:
    """
    Orchestrates processing of multiple PLACSP ZIP files.

    Ensures:
    1. ZIPs are processed in chronological order (oldest to newest)
    2. Each ZIP's base ATOM is correctly identified
    3. Syndication chains are properly followed
    """

    def __init__(self, session: Optional[requests.Session] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize orchestrator.

        Args:
            session: Optional requests.Session
            logger: Optional logger instance
        """
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self.date_extractor = PlacspZipDateExtractor()

    def discover_zips_from_url(self, base_url: str) -> list[PlacspZipInfo]:
        """
        Discover available PLACSP ZIP files from a base URL.

        Args:
            base_url: URL to directory listing (e.g., datosabiertos/)

        Returns:
            List of PlacspZipInfo objects

        Raises:
            Exception: If discovery fails
        """
        from bs4 import BeautifulSoup

        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            zips = []

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")

                # Look for PLACSP ZIP files
                if "PLACSP" in href and href.endswith(".zip"):
                    filename = href.split("/")[-1]
                    zip_info = PlacspZipInfo(filename=filename)

                    # Make absolute URL
                    if not href.startswith("http"):
                        zip_info.url = base_url.rstrip("/") + "/" + href.lstrip("/")
                    else:
                        zip_info.url = href

                    # Extract metadata
                    zip_info.date = self.date_extractor.extract_date(filename)
                    zip_info.syndication_id = self.date_extractor.extract_syndication_id(filename)

                    zips.append(zip_info)

            self.logger.info(f"Discovered {len(zips)} ZIP files")
            return zips

        except Exception as e:
            self.logger.error(f"Failed to discover ZIPs: {e}")
            raise

    def sort_zips_chronologically(self, zips: list[PlacspZipInfo]) -> list[PlacspZipInfo]:
        """
        Sort ZIPs in chronological order (oldest to newest).

        This is crucial for PLACSP syndication chains to work correctly.

        Args:
            zips: List of PlacspZipInfo objects

        Returns:
            Sorted list
        """
        # Separate ZIPs with dates from those without
        with_dates = [z for z in zips if z.date]
        without_dates = [z for z in zips if not z.date]

        # Sort those with dates
        with_dates.sort()

        # Log sorting
        for z in with_dates:
            self.logger.debug(f"ZIP order: {z.filename} ({z.date})")

        return with_dates + without_dates

    def identify_base_atom_filename(self, zip_info: PlacspZipInfo, zip_content: bytes) -> Optional[str]:
        """
        Identify the base ATOM filename within a ZIP.

        According to PLACSP spec, the base ATOM file is the entry point
        for syndication (e.g., "licitacionesPerfilesContratanteCompleto3.atom").

        Args:
            zip_info: PlacspZipInfo object
            zip_content: Raw ZIP file bytes

        Returns:
            Base ATOM filename or None
        """
        try:
            with ZipFile(BytesIO(zip_content)) as zf:
                atom_files = [f for f in zf.namelist() if f.endswith(".atom")]

                if not atom_files:
                    self.logger.warning(f"No ATOM file found in {zip_info.filename}")
                    return None

                # Look for the base ATOM (typically the one without a date suffix)
                base_atoms = [f for f in atom_files if not re.search(r"\d{6,8}", f)]

                if base_atoms:
                    base_atom = base_atoms[0]
                    zip_info.base_atom_filename = base_atom
                    self.logger.debug(f"Identified base ATOM: {base_atom}")
                    return base_atom

                # If no base atom without date, use the first one
                zip_info.base_atom_filename = atom_files[0]
                return atom_files[0]

        except Exception as e:
            self.logger.error(f"Failed to identify base ATOM in {zip_info.filename}: {e}")
            return None

    def extract_base_atom_content(self, zip_content: bytes, base_atom_filename: str) -> Optional[bytes]:
        """
        Extract the base ATOM file content from a ZIP.

        Args:
            zip_content: Raw ZIP file bytes
            base_atom_filename: Filename of base ATOM

        Returns:
            ATOM file content or None
        """
        try:
            with ZipFile(BytesIO(zip_content)) as zf:
                if base_atom_filename in zf.namelist():
                    return zf.read(base_atom_filename)
                else:
                    self.logger.error(f"ATOM file not found in ZIP: {base_atom_filename}")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to extract ATOM from ZIP: {e}")
            return None

    def fetch_and_prepare_zip(self, zip_info: PlacspZipInfo) -> tuple[bytes, Optional[str]]:
        """
        Fetch ZIP from URL and identify base ATOM.

        Args:
            zip_info: PlacspZipInfo object with URL

        Returns:
            Tuple of (zip_content, base_atom_filename)

        Raises:
            Exception: If fetching or processing fails
        """
        if not zip_info.url:
            raise ValueError(f"No URL for ZIP: {zip_info.filename}")

        try:
            self.logger.info(f"Fetching ZIP: {zip_info.url}")
            response = self.session.get(zip_info.url, timeout=60)
            response.raise_for_status()

            zip_content = response.content

            # Identify base ATOM
            base_atom = self.identify_base_atom_filename(zip_info, zip_content)

            return zip_content, base_atom

        except Exception as e:
            self.logger.error(f"Failed to fetch/prepare ZIP {zip_info.url}: {e}")
            raise

    def get_processing_order(self, zips: list[PlacspZipInfo]) -> list[PlacspZipInfo]:
        """
        Get the correct order to process ZIPs for proper syndication chain.

        Returns ZIPs sorted chronologically (oldest to newest).

        Args:
            zips: List of PlacspZipInfo objects

        Returns:
            Sorted list
        """
        self.logger.info(f"Determining processing order for {len(zips)} ZIPs")

        # Filter by syndication ID if multiple are present
        syndication_ids = {z.syndication_id for z in zips if z.syndication_id}
        if len(syndication_ids) > 1:
            self.logger.warning(f"Multiple syndication IDs found: {syndication_ids}")
            self.logger.info("Recommend processing each syndication separately")

        sorted_zips = self.sort_zips_chronologically(zips)

        self.logger.info("Processing order:")
        for i, z in enumerate(sorted_zips, 1):
            self.logger.info(f"  {i}. {z.filename} ({z.date})")

        return sorted_zips