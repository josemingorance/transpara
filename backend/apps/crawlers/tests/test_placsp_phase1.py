"""
Tests for PLACSP Phase 1 infrastructure (atom_parser, fields_extractor, zip_orchestrator).

Tests the new robust ATOM parsing, field extraction, and ZIP orchestration modules.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from io import BytesIO
from zipfile import ZipFile

from apps.crawlers.implementations.atom_parser import (
    AtomParser,
    AtomParseError,
    AtomEntry,
    AtomFeed,
    AtomZipHandler,
    SyndicationChainFollower,
)
from apps.crawlers.implementations.placsp_fields_extractor import (
    PlacspFieldsExtractor,
    PlacspLicitacion,
    ContractLot,
    AwardedCompany,
    ContractResult,
)
from apps.crawlers.implementations.zip_orchestrator import (
    ZipOrchestrator,
    PlacspZipInfo,
    PlacspZipDateExtractor,
)


# ============================================================================
# SAMPLE DATA FOR TESTS
# ============================================================================

SAMPLE_ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <id>urn:uuid:60a76c80-d399-11d9-b91C-0003939e0af6</id>
    <title>PLACSP Licitaciones - Enero 2021</title>
    <updated>2021-01-31T23:59:59Z</updated>
    <link rel="self" href="/datos/licitacionesPerfilesContratanteCompleto3.atom"/>
    <link rel="previous-archive" href="/datos/licitacionesPerfilesContratanteCompleto3_202012.atom"/>
    <entry>
        <id>urn:uuid:1234-5678</id>
        <title>Servicio de consultoría</title>
        <updated>2021-01-15T10:30:00Z</updated>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                <pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
                    <pcsp:codigoExpediente>2021-CONS-001</pcsp:codigoExpediente>
                    <pcsp:objetoContrato>Servicios de consultoría técnica</pcsp:objetoContrato>
                    <pcsp:presupuestoSinImpuestos>100000.00</pcsp:presupuestoSinImpuestos>
                    <pcsp:presupuestoConImpuestos>121000.00</pcsp:presupuestoConImpuestos>
                    <pcsp:tipoContrato>Servicios</pcsp:tipoContrato>
                    <pcsp:cpv>72000000-2</pcsp:cpv>
                    <pcsp:organoContratacion>Ministerio de Ejemplo</pcsp:organoContratacion>
                    <pcsp:estado>VIGENTE</pcsp:estado>
                    <pcsp:fase>Pendiente de adjudicación</pcsp:fase>
                </pcsp:licitacion>
            </div>
        </content>
    </entry>
</feed>
"""

SAMPLE_ATOM_WITH_LOTS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <id>urn:uuid:test-lotes</id>
    <title>Test Feed with Lots</title>
    <updated>2021-01-31T23:59:59Z</updated>
    <entry>
        <id>urn:uuid:multi-lot</id>
        <title>Contrato con múltiples lotes</title>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
                <pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
                    <pcsp:codigoExpediente>2021-ML-001</pcsp:codigoExpediente>
                    <pcsp:objetoContrato>Contrato principal</pcsp:objetoContrato>
                    <pcsp:lote>
                        <pcsp:numeroLote>1</pcsp:numeroLote>
                        <pcsp:objeto>Lote 1 - Suministro A</pcsp:objeto>
                        <pcsp:presupuestoSinImpuestos>50000.00</pcsp:presupuestoSinImpuestos>
                    </pcsp:lote>
                    <pcsp:lote>
                        <pcsp:numeroLote>2</pcsp:numeroLote>
                        <pcsp:objeto>Lote 2 - Suministro B</pcsp:objeto>
                        <pcsp:presupuestoSinImpuestos>75000.00</pcsp:presupuestoSinImpuestos>
                    </pcsp:lote>
                    <pcsp:resultado>
                        <pcsp:numeroLote>1</pcsp:numeroLote>
                        <pcsp:estado>Adjudicado</pcsp:estado>
                        <pcsp:adjudicatario>
                            <pcsp:denominacion>Empresa A S.L.</pcsp:denominacion>
                            <pcsp:identificador>A12345678</pcsp:identificador>
                            <pcsp:importeAdjudicacionSinImpuestos>48000.00</pcsp:importeAdjudicacionSinImpuestos>
                        </pcsp:adjudicatario>
                    </pcsp:resultado>
                    <pcsp:resultado>
                        <pcsp:numeroLote>2</pcsp:numeroLote>
                        <pcsp:estado>Adjudicado</pcsp:estado>
                        <pcsp:adjudicatario>
                            <pcsp:denominacion>Empresa B S.A.</pcsp:denominacion>
                            <pcsp:identificador>B87654321</pcsp:identificador>
                            <pcsp:importeAdjudicacionSinImpuestos>70000.00</pcsp:importeAdjudicacionSinImpuestos>
                        </pcsp:adjudicatario>
                    </pcsp:resultado>
                </pcsp:licitacion>
            </div>
        </content>
    </entry>
</feed>
"""


# ============================================================================
# ATOM PARSER TESTS
# ============================================================================


class TestAtomParser:
    """Test ATOM feed parsing."""

    def test_parse_atom_bytes_success(self):
        """Test successful ATOM feed parsing."""
        parser = AtomParser()
        feed = parser.parse_atom_bytes(SAMPLE_ATOM_FEED.encode("utf-8"))

        assert feed.feed_id == "urn:uuid:60a76c80-d399-11d9-b91C-0003939e0af6"
        assert feed.title == "PLACSP Licitaciones - Enero 2021"
        assert len(feed.entries) == 1
        assert feed.next_url == "/datos/licitacionesPerfilesContratanteCompleto3_202012.atom"

    def test_parse_atom_entry(self):
        """Test parsing individual ATOM entry."""
        parser = AtomParser()
        feed = parser.parse_atom_bytes(SAMPLE_ATOM_FEED.encode("utf-8"))

        entry = feed.entries[0]
        assert entry.entry_id == "urn:uuid:1234-5678"
        assert entry.title == "Servicio de consultoría"
        assert entry.updated == "2021-01-15T10:30:00Z"
        assert entry.content is not None

    def test_parse_invalid_xml(self):
        """Test parsing invalid XML raises error."""
        parser = AtomParser()

        with pytest.raises(AtomParseError):
            parser.parse_atom_bytes(b"invalid xml <unclosed")

    def test_parse_missing_feed_id(self):
        """Test parsing feed without ID raises error."""
        invalid_feed = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>No ID Feed</title>
        </feed>
        """
        parser = AtomParser()

        with pytest.raises(AtomParseError):
            parser.parse_atom_bytes(invalid_feed.encode("utf-8"))

    def test_extract_namespaced_text(self):
        """Test extracting namespaced text."""
        parser = AtomParser()
        import xml.etree.ElementTree as ET

        xml_str = """<root xmlns:pcsp="http://www.plataforma.es/pcsp">
            <pcsp:codigoExpediente>2021-001</pcsp:codigoExpediente>
        </root>"""

        root = ET.fromstring(xml_str)
        text = parser.extract_namespaced_text(root, "pcsp:codigoExpediente")
        assert text == "2021-001"


class TestAtomZipHandler:
    """Test ZIP extraction and ATOM parsing."""

    def test_extract_atom_from_zip(self):
        """Test extracting ATOM from ZIP file."""
        # Create a test ZIP
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("licitaciones.atom", SAMPLE_ATOM_FEED.encode("utf-8"))

        zip_content = zip_buffer.getvalue()

        handler = AtomZipHandler()
        feed = handler.extract_atom_from_zip(zip_content, "licitaciones.atom")

        assert feed is not None
        assert len(feed.entries) == 1
        assert feed.source_file == "licitaciones.atom"

    def test_extract_atom_auto_detect_filename(self):
        """Test auto-detection of ATOM filename in ZIP."""
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("base.atom", SAMPLE_ATOM_FEED.encode("utf-8"))

        zip_content = zip_buffer.getvalue()

        handler = AtomZipHandler()
        feed = handler.extract_atom_from_zip(zip_content)

        assert feed is not None
        assert feed.source_file == "base.atom"

    def test_extract_all_xml_files(self):
        """Test extracting all XML files from ZIP."""
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("file1.atom", b"<feed/>")
            zf.writestr("file2.xml", b"<data/>")
            zf.writestr("readme.txt", b"text")

        zip_content = zip_buffer.getvalue()

        handler = AtomZipHandler()
        files = handler.get_all_xml_files_from_zip(zip_content)

        assert len(files) == 2
        assert "file1.atom" in files
        assert "file2.xml" in files
        assert "readme.txt" not in files


class TestSyndicationChainFollower:
    """Test syndication chain following."""

    @patch("apps.crawlers.implementations.atom_parser.requests.Session.get")
    def test_follow_chain_single_feed(self, mock_get):
        """Test following chain with single feed (end of chain)."""
        # Create feed without next_url to indicate end of chain
        single_feed = SAMPLE_ATOM_FEED.replace(
            '<link rel="previous-archive" href="/datos/licitacionesPerfilesContratanteCompleto3_202012.atom"/>', ""
        )

        mock_response = Mock()
        mock_response.content = single_feed.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        follower = SyndicationChainFollower()
        feeds = follower.follow_chain("http://example.com/feed.atom")

        # Should only fetch once since there's no next_url
        assert len(feeds) == 1
        assert feeds[0].entries[0].entry_id == "urn:uuid:1234-5678"
        assert mock_get.call_count == 1

    @patch("apps.crawlers.implementations.atom_parser.requests.Session.get")
    def test_follow_chain_multiple_feeds(self, mock_get):
        """Test following chain with multiple feeds."""
        # Create a feed with reference to previous
        feed2 = SAMPLE_ATOM_FEED.replace(
            "urn:uuid:60a76c80-d399-11d9-b91C-0003939e0af6", "urn:uuid:december-2020"
        ).replace("Enero 2021", "Diciembre 2020")

        feed2_no_link = feed2.replace(
            '<link rel="previous-archive" href="/datos/licitacionesPerfilesContratanteCompleto3_202012.atom"/>',
            "",
        )

        responses = [
            Mock(content=SAMPLE_ATOM_FEED.encode("utf-8")),
            Mock(content=feed2_no_link.encode("utf-8")),
        ]

        mock_get.side_effect = responses
        for resp in responses:
            resp.raise_for_status = Mock()

        follower = SyndicationChainFollower()
        feeds = follower.follow_chain("http://example.com/feed.atom")

        # Should get both feeds in chronological order (oldest first)
        assert len(feeds) == 2
        assert feeds[0].feed_id == "urn:uuid:december-2020"  # Oldest first


# ============================================================================
# FIELDS EXTRACTOR TESTS
# ============================================================================


class TestPlacspFieldsExtractor:
    """Test PLACSP field extraction."""

    def test_extract_basic_fields(self):
        """Test extracting basic licitacion fields."""
        extractor = PlacspFieldsExtractor()

        # Create a simpler test XML with just the PCSpelicitacion content
        test_xml = """<pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
            <pcsp:codigoExpediente>2021-CONS-001</pcsp:codigoExpediente>
            <pcsp:objetoContrato>Servicios de consultoría técnica</pcsp:objetoContrato>
            <pcsp:presupuestoSinImpuestos>100000.00</pcsp:presupuestoSinImpuestos>
            <pcsp:presupuestoConImpuestos>121000.00</pcsp:presupuestoConImpuestos>
            <pcsp:tipoContrato>Servicios</pcsp:tipoContrato>
            <pcsp:cpv>72000000-2</pcsp:cpv>
            <pcsp:organoContratacion>Ministerio de Ejemplo</pcsp:organoContratacion>
            <pcsp:estado>VIGENTE</pcsp:estado>
            <pcsp:fase>Pendiente de adjudicación</pcsp:fase>
        </pcsp:licitacion>"""

        licitacion = extractor.extract_from_atom_entry_xml(test_xml, "urn:uuid:1234-5678")

        assert licitacion is not None
        assert licitacion.identifier == "urn:uuid:1234-5678"
        assert licitacion.expedition_number == "2021-CONS-001"
        assert licitacion.contract_object == "Servicios de consultoría técnica"
        assert licitacion.budget_without_taxes == Decimal("100000.00")
        assert licitacion.budget_with_taxes == Decimal("121000.00")
        assert licitacion.contract_type == "Servicios"

    def test_extract_lots(self):
        """Test extracting lots from licitacion."""
        extractor = PlacspFieldsExtractor()

        test_xml = """<pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
            <pcsp:codigoExpediente>2021-ML-001</pcsp:codigoExpediente>
            <pcsp:objetoContrato>Contrato principal</pcsp:objetoContrato>
            <pcsp:lote>
                <pcsp:numeroLote>1</pcsp:numeroLote>
                <pcsp:objeto>Lote 1 - Suministro A</pcsp:objeto>
                <pcsp:presupuestoSinImpuestos>50000.00</pcsp:presupuestoSinImpuestos>
            </pcsp:lote>
            <pcsp:lote>
                <pcsp:numeroLote>2</pcsp:numeroLote>
                <pcsp:objeto>Lote 2 - Suministro B</pcsp:objeto>
                <pcsp:presupuestoSinImpuestos>75000.00</pcsp:presupuestoSinImpuestos>
            </pcsp:lote>
        </pcsp:licitacion>"""

        licitacion = extractor.extract_from_atom_entry_xml(test_xml, "urn:uuid:multi-lot")

        assert licitacion is not None
        assert len(licitacion.lots) == 2

        assert licitacion.lots[0].lot_number == "1"
        assert licitacion.lots[0].object == "Lote 1 - Suministro A"
        assert licitacion.lots[0].budget_without_taxes == Decimal("50000.00")

        assert licitacion.lots[1].lot_number == "2"
        assert licitacion.lots[1].object == "Lote 2 - Suministro B"

    def test_extract_results_with_awarded_companies(self):
        """Test extracting results and awarded companies."""
        extractor = PlacspFieldsExtractor()

        test_xml = """<pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
            <pcsp:codigoExpediente>2021-ML-001</pcsp:codigoExpediente>
            <pcsp:objetoContrato>Contrato principal</pcsp:objetoContrato>
            <pcsp:resultado>
                <pcsp:numeroLote>1</pcsp:numeroLote>
                <pcsp:estado>Adjudicado</pcsp:estado>
                <pcsp:adjudicatario>
                    <pcsp:denominacion>Empresa A S.L.</pcsp:denominacion>
                    <pcsp:identificador>A12345678</pcsp:identificador>
                    <pcsp:importeAdjudicacionSinImpuestos>48000.00</pcsp:importeAdjudicacionSinImpuestos>
                </pcsp:adjudicatario>
            </pcsp:resultado>
            <pcsp:resultado>
                <pcsp:numeroLote>2</pcsp:numeroLote>
                <pcsp:estado>Adjudicado</pcsp:estado>
                <pcsp:adjudicatario>
                    <pcsp:denominacion>Empresa B S.A.</pcsp:denominacion>
                    <pcsp:identificador>B87654321</pcsp:identificador>
                    <pcsp:importeAdjudicacionSinImpuestos>70000.00</pcsp:importeAdjudicacionSinImpuestos>
                </pcsp:adjudicatario>
            </pcsp:resultado>
        </pcsp:licitacion>"""

        licitacion = extractor.extract_from_atom_entry_xml(test_xml, "urn:uuid:multi-lot")

        assert len(licitacion.results) == 2

        # Check first result
        result1 = licitacion.results[0]
        assert result1.lot_number == "1"
        assert result1.result_status == "Adjudicado"
        assert len(result1.awarded_companies) == 1

        company1 = result1.awarded_companies[0]
        assert company1.name == "Empresa A S.L."
        assert company1.identifier == "A12345678"
        assert company1.award_amount_without_taxes == Decimal("48000.00")

    def test_to_dict_conversion(self):
        """Test converting licitacion to dict."""
        extractor = PlacspFieldsExtractor()

        test_xml = """<pcsp:licitacion xmlns:pcsp="http://www.plataforma.es/pcsp">
            <pcsp:codigoExpediente>2021-CONS-001</pcsp:codigoExpediente>
            <pcsp:objetoContrato>Servicios de consultoría técnica</pcsp:objetoContrato>
            <pcsp:presupuestoSinImpuestos>100000.00</pcsp:presupuestoSinImpuestos>
            <pcsp:presupuestoConImpuestos>121000.00</pcsp:presupuestoConImpuestos>
        </pcsp:licitacion>"""

        licitacion = extractor.extract_from_atom_entry_xml(test_xml, "urn:uuid:1234-5678")
        data = licitacion.to_dict()

        assert isinstance(data, dict)
        assert data["identifier"] == "urn:uuid:1234-5678"
        # Decimals should be converted to float
        assert isinstance(data["budget_without_taxes"], float)
        assert data["budget_without_taxes"] == 100000.0


# ============================================================================
# ZIP ORCHESTRATOR TESTS
# ============================================================================


class TestPlacspZipDateExtractor:
    """Test ZIP date extraction."""

    def test_extract_date_yyyymm(self):
        """Test extracting date from YYYYMM format."""
        filename = "licitacionesPerfilesContratanteCompleto3_202101.zip"
        date = PlacspZipDateExtractor.extract_date(filename)

        assert date is not None
        assert date.year == 2021
        assert date.month == 1

    def test_extract_date_yyyy(self):
        """Test extracting date from YYYY format."""
        filename = "licitacionesPerfilesContratanteCompleto3_2020.zip"
        date = PlacspZipDateExtractor.extract_date(filename)

        assert date is not None
        assert date.year == 2020
        assert date.month == 1

    def test_extract_syndication_id(self):
        """Test extracting syndication ID."""
        filename = "licitacionesPerfilesContratanteCompleto3_202101.zip"
        synd_id = PlacspZipDateExtractor.extract_syndication_id(filename)

        assert synd_id == "3"

    def test_invalid_month(self):
        """Test handling invalid month."""
        filename = "licitacionesPerfilesContratanteCompleto3_202113.zip"
        date = PlacspZipDateExtractor.extract_date(filename)

        # Should fall back to YYYY extraction
        assert date is None  # No YYYY pattern


class TestZipOrchestrator:
    """Test ZIP orchestration."""

    def test_sort_zips_chronologically(self):
        """Test sorting ZIPs by date."""
        orchestrator = ZipOrchestrator()

        zips = [
            PlacspZipInfo(filename="file_202103.zip", date=datetime(2021, 3, 1)),
            PlacspZipInfo(filename="file_202101.zip", date=datetime(2021, 1, 1)),
            PlacspZipInfo(filename="file_202102.zip", date=datetime(2021, 2, 1)),
        ]

        sorted_zips = orchestrator.sort_zips_chronologically(zips)

        assert sorted_zips[0].filename == "file_202101.zip"
        assert sorted_zips[1].filename == "file_202102.zip"
        assert sorted_zips[2].filename == "file_202103.zip"

    def test_identify_base_atom_filename(self):
        """Test identifying base ATOM filename in ZIP."""
        orchestrator = ZipOrchestrator()

        # Create test ZIP
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("licitacionesPerfilesContratanteCompleto3.atom", b"<feed/>")
            zf.writestr("licitacionesPerfilesContratanteCompleto3_202101.atom", b"<feed/>")

        zip_info = PlacspZipInfo(filename="test.zip")
        base_atom = orchestrator.identify_base_atom_filename(zip_info, zip_buffer.getvalue())

        # Should identify the one without date suffix
        assert base_atom == "licitacionesPerfilesContratanteCompleto3.atom"

    def test_processing_order(self):
        """Test getting correct processing order."""
        orchestrator = ZipOrchestrator()

        zips = [
            PlacspZipInfo(
                filename="licitaciones_202103.zip",
                date=datetime(2021, 3, 1),
                syndication_id="643",
            ),
            PlacspZipInfo(
                filename="licitaciones_202101.zip",
                date=datetime(2021, 1, 1),
                syndication_id="643",
            ),
            PlacspZipInfo(
                filename="licitaciones_202102.zip",
                date=datetime(2021, 2, 1),
                syndication_id="643",
            ),
        ]

        ordered = orchestrator.get_processing_order(zips)

        # Should be oldest to newest
        assert ordered[0].filename == "licitaciones_202101.zip"
        assert ordered[1].filename == "licitaciones_202102.zip"
        assert ordered[2].filename == "licitaciones_202103.zip"


class TestPlacspZipInfo:
    """Test PlacspZipInfo dataclass."""

    def test_comparison(self):
        """Test comparing PlacspZipInfo by date."""
        zip1 = PlacspZipInfo(filename="file1.zip", date=datetime(2021, 1, 1))
        zip2 = PlacspZipInfo(filename="file2.zip", date=datetime(2021, 2, 1))

        assert zip1 < zip2

    def test_comparison_without_dates(self):
        """Test comparing without dates uses filename."""
        zip1 = PlacspZipInfo(filename="aaa.zip")
        zip2 = PlacspZipInfo(filename="zzz.zip")

        assert zip1 < zip2
