"""
ATOM/XML feed parser for PLACSP Datos Abiertos.

Handles the traversal of syndication chains where each ATOM feed
references the next one chronologically. This allows processing
of complete historical data while maintaining temporal order.
"""
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO
from typing import Optional
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile

import requests


@dataclass
class AtomEntry:
    """Represents a single entry in an ATOM feed."""

    entry_id: str
    title: str
    updated: Optional[str] = None
    content: Optional[str] = None
    raw_element: Optional[ET.Element] = None


@dataclass
class AtomFeed:
    """Represents an ATOM feed with metadata and entries."""

    feed_id: str
    title: str
    entries: list[AtomEntry]
    updated: Optional[str] = None
    next_url: Optional[str] = None  # Link to previous feed in chain
    source_file: Optional[str] = None


class AtomNamespaces:
    """ATOM and related XML namespaces."""

    ATOM = "http://www.w3.org/2005/Atom"
    XHTML = "http://www.w3.org/1999/xhtml"
    PCSP = "http://www.plataforma.es/pcsp"
    CODICE = "http://www.plataforma.es/codice"


class AtomParseError(Exception):
    """Exception raised during ATOM parsing."""

    pass


class AtomParser:
    """
    Parser for PLACSP ATOM/XML feeds.

    Handles:
    - Parsing ATOM feeds with proper namespace handling
    - Following syndication chains (each feed links to previous)
    - Extracting entries with content and metadata
    - Handling both inline content and references
    """

    def __init__(self, session: Optional[requests.Session] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize ATOM parser.

        Args:
            session: Optional requests.Session for HTTP requests
            logger: Optional logger instance
        """
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)

        # Namespaces for XPath queries
        self.ns = {
            "atom": AtomNamespaces.ATOM,
            "xhtml": AtomNamespaces.XHTML,
            "pcsp": AtomNamespaces.PCSP,
            "codice": AtomNamespaces.CODICE,
        }

    def parse_atom_bytes(self, xml_content: bytes, source_file: Optional[str] = None) -> AtomFeed:
        """
        Parse ATOM feed from bytes.

        Args:
            xml_content: Raw XML bytes
            source_file: Optional filename for reference

        Returns:
            AtomFeed object with entries and metadata

        Raises:
            AtomParseError: If parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
            return self._parse_feed_root(root, source_file=source_file)
        except ET.ParseError as e:
            raise AtomParseError(f"Failed to parse XML: {e}")
        except Exception as e:
            raise AtomParseError(f"Unexpected error parsing ATOM: {e}")

    def parse_atom_file(self, file_path: str) -> AtomFeed:
        """
        Parse ATOM feed from file path.

        Args:
            file_path: Path to ATOM/XML file

        Returns:
            AtomFeed object

        Raises:
            AtomParseError: If file reading or parsing fails
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return self.parse_atom_bytes(content, source_file=file_path)
        except IOError as e:
            raise AtomParseError(f"Failed to read ATOM file: {e}")

    def _parse_feed_root(self, root: ET.Element, source_file: Optional[str] = None) -> AtomFeed:
        """
        Parse the root feed element.

        Args:
            root: Root XML element
            source_file: Optional source filename

        Returns:
            AtomFeed object

        Raises:
            AtomParseError: If feed structure is invalid
        """
        # Get feed metadata
        feed_id = self._get_text(root, "atom:id")
        title = self._get_text(root, "atom:title")
        updated = self._get_text(root, "atom:updated")

        if not feed_id:
            raise AtomParseError("Feed missing required 'id' element")

        # Parse all entries
        entries = []
        for entry_elem in root.findall("atom:entry", self.ns):
            try:
                entry = self._parse_entry(entry_elem)
                entries.append(entry)
            except Exception as e:
                self.logger.warning(f"Failed to parse entry: {e}")
                continue

        # Find link to previous feed (rel="previous-archive")
        next_url = self._find_next_url(root)

        feed = AtomFeed(
            feed_id=feed_id,
            title=title or "Unknown",
            entries=entries,
            updated=updated,
            next_url=next_url,
            source_file=source_file,
        )

        self.logger.debug(f"Parsed ATOM feed: {feed_id} with {len(entries)} entries")
        return feed

    def _parse_entry(self, entry_elem: ET.Element) -> AtomEntry:
        """
        Parse a single ATOM entry.

        Args:
            entry_elem: Entry XML element

        Returns:
            AtomEntry object

        Raises:
            Exception: If required fields are missing
        """
        entry_id = self._get_text(entry_elem, "atom:id")
        title = self._get_text(entry_elem, "atom:title")

        if not entry_id or not title:
            raise ValueError("Entry missing 'id' or 'title'")

        # Extract content (may be embedded XML or text)
        content_elem = entry_elem.find("atom:content", self.ns)
        content = None
        if content_elem is not None:
            # Content can be text or embedded XML
            if content_elem.text:
                content = content_elem.text
            else:
                # Check for embedded XML elements
                if len(content_elem) > 0:
                    content = ET.tostring(content_elem[0], encoding="unicode")

        updated = self._get_text(entry_elem, "atom:updated")

        return AtomEntry(
            entry_id=entry_id,
            title=title,
            updated=updated,
            content=content,
            raw_element=entry_elem,
        )

    def _find_next_url(self, root: ET.Element) -> Optional[str]:
        """
        Find the link to the previous ATOM feed in the syndication chain.

        In PLACSP, each ATOM feed has a link with rel="previous-archive"
        pointing to the next historical feed to process.

        Args:
            root: Root XML element

        Returns:
            URL of next feed to process, or None if at end of chain
        """
        for link_elem in root.findall("atom:link", self.ns):
            rel = link_elem.get("rel", "")
            href = link_elem.get("href")

            if rel == "previous-archive" and href:
                return href

        return None

    def _get_text(self, elem: ET.Element, tag: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get text content from element by tag name.

        Handles namespace-prefixed tags.

        Args:
            elem: XML element
            tag: Tag name (with namespace prefix like 'atom:title')
            default: Default value if not found

        Returns:
            Text content or default
        """
        found = elem.find(tag, self.ns)
        if found is not None and found.text:
            return found.text.strip()
        return default

    def extract_namespaced_text(self, elem: ET.Element, namespaced_tag: str) -> Optional[str]:
        """
        Extract text from a namespaced element.

        Args:
            elem: XML element
            namespaced_tag: Tag with namespace (e.g., 'pcsp:codigoExpediente')

        Returns:
            Text content or None
        """
        return self._get_text(elem, namespaced_tag)


class AtomZipHandler:
    """
    Handler for ZIP files containing ATOM feeds.

    PLACSP provides data in ZIP files where:
    - Each ZIP contains one base ATOM file (e.g., licitacionesPerfilesContratanteCompleto3.atom)
    - The ATOM file may contain additional XML files as entries
    - Multiple ZIPs should be processed in chronological order
    """

    def __init__(self, session: Optional[requests.Session] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize ZIP handler.

        Args:
            session: Optional requests.Session
            logger: Optional logger instance
        """
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self.parser = AtomParser(session=session, logger=logger)

    def extract_atom_from_zip(self, zip_content: bytes, atom_filename: Optional[str] = None) -> Optional[AtomFeed]:
        """
        Extract and parse ATOM feed from ZIP file.

        Args:
            zip_content: Raw ZIP file bytes
            atom_filename: Specific ATOM filename to extract (optional)

        Returns:
            AtomFeed object or None if not found

        Raises:
            AtomParseError: If ZIP or ATOM parsing fails
        """
        try:
            with ZipFile(BytesIO(zip_content)) as zf:
                # If filename not specified, look for .atom file
                if not atom_filename:
                    atom_files = [name for name in zf.namelist() if name.endswith(".atom")]
                    if not atom_files:
                        raise AtomParseError("No .atom file found in ZIP")
                    atom_filename = atom_files[0]

                if atom_filename not in zf.namelist():
                    raise AtomParseError(f"ATOM file not found: {atom_filename}")

                atom_content = zf.read(atom_filename)
                return self.parser.parse_atom_bytes(atom_content, source_file=atom_filename)

        except ZipFile.BadZipFile as e:
            raise AtomParseError(f"Invalid ZIP file: {e}")
        except Exception as e:
            raise AtomParseError(f"Failed to extract ATOM from ZIP: {e}")

    def get_all_xml_files_from_zip(self, zip_content: bytes) -> dict[str, bytes]:
        """
        Extract all XML/ATOM files from ZIP.

        Args:
            zip_content: Raw ZIP file bytes

        Returns:
            Dictionary of {filename: content}
        """
        xml_files = {}
        try:
            with ZipFile(BytesIO(zip_content)) as zf:
                for name in zf.namelist():
                    if name.endswith((".xml", ".atom")):
                        xml_files[name] = zf.read(name)
        except Exception as e:
            self.logger.error(f"Failed to extract XML files from ZIP: {e}")

        return xml_files


class SyndicationChainFollower:
    """
    Follows the syndication chain of ATOM feeds.

    In PLACSP:
    1. Start with the most recent ATOM feed (e.g., March 2021)
    2. Each feed has a link to the previous month's feed
    3. Continue until reaching the oldest feed
    4. This creates a chain: March -> February -> January

    This follower manages that chain traversal.
    """

    def __init__(self, session: Optional[requests.Session] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize chain follower.

        Args:
            session: Optional requests.Session
            logger: Optional logger instance
        """
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self.parser = AtomParser(session=session, logger=logger)
        self.visited_urls = set()

    def follow_chain(self, start_url: str, max_iterations: int = 100) -> list[AtomFeed]:
        """
        Follow the syndication chain from a starting URL.

        Args:
            start_url: URL to the most recent ATOM feed
            max_iterations: Maximum feeds to follow (prevent infinite loops)

        Returns:
            List of AtomFeed objects in chronological order (oldest to newest)

        Raises:
            AtomParseError: If fetching or parsing fails
        """
        feeds = []
        current_url: Optional[str] = start_url
        iteration = 0

        self.logger.info(f"Starting syndication chain from: {start_url}")

        while current_url and iteration < max_iterations:
            iteration += 1

            # Prevent infinite loops
            if current_url in self.visited_urls:
                self.logger.warning(f"Circular reference detected: {current_url}")
                break

            self.visited_urls.add(current_url)

            try:
                self.logger.debug(f"Fetching feed [{iteration}]: {current_url}")
                response = self.session.get(current_url, timeout=30)
                response.raise_for_status()

                feed = self.parser.parse_atom_bytes(response.content, source_file=current_url)
                feeds.append(feed)

                self.logger.info(f"Fetched feed: {feed.feed_id} with {len(feed.entries)} entries")

                # Get next URL in chain
                next_url = feed.next_url

                if not next_url:
                    # No more feeds in chain
                    break

                # Handle relative URLs
                if not next_url.startswith("http"):
                    base = urlparse(current_url)
                    next_url = f"{base.scheme}://{base.netloc}{next_url}"

                current_url = next_url

            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch feed at iteration {iteration}: {e}")
                break
            except AtomParseError as e:
                self.logger.error(f"Failed to parse feed at iteration {iteration}: {e}")
                break

        # Return in chronological order (oldest to newest)
        feeds.reverse()
        self.logger.info(f"Followed {len(feeds)} feeds in chain")
        return feeds

    def reset(self):
        """Reset visited URLs tracking."""
        self.visited_urls.clear()