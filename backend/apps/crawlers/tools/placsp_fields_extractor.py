"""
PLACSP Fields Extractor.

Extracts all available fields from PLACSP ATOM entries according to the
OpenPLACSP manual specification. Handles both licitaciones (tenders) and
resultados (awards) with multiple lots and adjudicatarios.
"""
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from typing import Any, Optional


@dataclass
class ContractLot:
    """Represents a single lot in a contract."""

    lot_number: Optional[str] = None
    object: Optional[str] = None  # Objeto del lote
    budget_without_taxes: Optional[Decimal] = None
    budget_with_taxes: Optional[Decimal] = None
    cpv_code: Optional[str] = None
    execution_place: Optional[str] = None


@dataclass
class AwardedCompany:
    """Represents an awarded company for a lot."""

    name: Optional[str] = None
    identifier_type: Optional[str] = None  # NIF, UTE, Otros
    identifier: Optional[str] = None
    is_pyme: Optional[bool] = None
    award_amount_without_taxes: Optional[Decimal] = None
    award_amount_with_taxes: Optional[Decimal] = None


@dataclass
class ContractResult:
    """Represents the result/award information for a lot."""

    lot_number: Optional[str] = None
    result_status: Optional[str] = None  # Adjudicado, Formalizado, Desierto, etc
    award_date: Optional[str] = None
    num_offers_received: Optional[int] = None
    lowest_offer_amount: Optional[Decimal] = None
    highest_offer_amount: Optional[Decimal] = None
    abnormally_low_offers_excluded: Optional[bool] = None
    contract_number: Optional[str] = None
    contract_formalization_date: Optional[str] = None
    contract_effective_date: Optional[str] = None
    awarded_companies: list[AwardedCompany] = field(default_factory=list)


@dataclass
class PlacspLicitacion:
    """
    Complete PLACSP licitacion (tender) with all fields from the manual.

    This represents the "Licitaciones" sheet from OpenPLACSP manual (Section 5.1).
    """

    # Required identifiers
    identifier: str
    link: str
    update_date: str

    # Status
    status: Optional[str] = None  # Vigente, Anulada, Archivada
    status_phase: Optional[str] = None  # Anuncio previo, En plazo, Pendiente, Adjudicada, Resuelta, Anulada
    first_publication_date: Optional[str] = None
    expedition_number: Optional[str] = None

    # Description
    contract_object: Optional[str] = None
    contract_type: Optional[str] = None  # Obras, Servicios, Suministros, etc
    cpv_code: Optional[str] = None

    # Budget information
    estimated_value: Optional[Decimal] = None
    budget_without_taxes: Optional[Decimal] = None
    budget_with_taxes: Optional[Decimal] = None

    # Location
    execution_place_nuts: Optional[str] = None
    execution_place_name: Optional[str] = None
    postal_code: Optional[str] = None

    # Contracting authority
    contracting_authority: Optional[str] = None
    authority_id_placsp: Optional[str] = None
    authority_tax_id: Optional[str] = None
    authority_dir3: Optional[str] = None
    authority_profile_link: Optional[str] = None

    # Administration type
    administration_type: Optional[str] = None  # AGE, CCAA, Local, etc

    # Procedure details
    procedure_type: Optional[str] = None  # Abierto, Restringido, Negociado, etc
    system_type: Optional[str] = None  # Contrato, Acuerdo Marco, etc
    processing_type: Optional[str] = None  # Ordinaria, Urgente, Emergencia
    offer_presentation_form: Optional[str] = None  # Manual, Electrónica, etc

    # Directive
    applicable_directive: Optional[str] = None

    # Subcontracting
    subcontracting_allowed: Optional[bool] = None
    subcontracting_percentage: Optional[Decimal] = None

    # Lots
    lots: list[ContractLot] = field(default_factory=list)

    # Results (awards)
    results: list[ContractResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, handling nested dataclasses and Decimals."""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, Decimal):
                result[key] = float(value) if value else None
            elif isinstance(value, list):
                # Handle nested dataclasses
                result[key] = [
                    item.to_dict() if hasattr(item, "to_dict") else item for item in value
                ]
            else:
                result[key] = value
        return result


class PlacspFieldsExtractor:
    """
    Extract PLACSP fields from ATOM entry content.

    Parses the embedded XML content in ATOM entries according to
    CODICE specification and extracts all available fields.
    """

    # Namespaces
    NAMESPACES = {
        "pcsp": "http://www.plataforma.es/pcsp",
        "codice": "http://www.plataforma.es/codice",
        "atom": "http://www.w3.org/2005/Atom",
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize extractor."""
        self.logger = logger or logging.getLogger(__name__)

    def extract_from_atom_entry_xml(self, entry_xml: str, entry_id: str) -> Optional[PlacspLicitacion]:
        """
        Extract PLACSP fields from ATOM entry content XML.

        Args:
            entry_xml: XML content (string) from ATOM entry
            entry_id: ATOM entry ID for reference

        Returns:
            PlacspLicitacion object or None if parsing fails
        """
        try:
            # Parse the embedded XML
            if not entry_xml:
                return None

            root = ET.fromstring(entry_xml)
            return self._extract_from_root(root, entry_id)

        except ET.ParseError as e:
            self.logger.warning(f"Failed to parse entry XML {entry_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting fields from {entry_id}: {e}")
            return None

    def extract_from_atom_entry_element(self, entry_elem: ET.Element, entry_id: str) -> Optional[PlacspLicitacion]:
        """
        Extract PLACSP fields from ATOM entry CODICE XML element.

        This handles the current PLACSP format where data is in ContractFolderStatus
        element instead of embedded in atom:content.

        Args:
            entry_elem: ATOM entry XML element
            entry_id: ATOM entry ID for reference

        Returns:
            PlacspLicitacion object or None if parsing fails
        """
        try:
            if entry_elem is None:
                return None

            # Find ContractFolderStatus (CODICE structure)
            # Try both possible namespace URIs
            codice_ns_ext_agg = "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2"
            codice_ns_agg = "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2"

            contract_folder = entry_elem.find(f"{{{codice_ns_ext_agg}}}ContractFolderStatus")
            if contract_folder is None:
                contract_folder = entry_elem.find(f"{{{codice_ns_agg}}}ContractFolderStatus")

            if contract_folder is None:
                self.logger.debug(f"No ContractFolderStatus found in entry {entry_id}")
                return None

            return self._extract_from_codice(contract_folder, entry_id, entry_elem)

        except Exception as e:
            self.logger.debug(f"Error extracting CODICE fields from {entry_id}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def _extract_from_codice(self, contract_folder: ET.Element, entry_id: str, entry_elem: ET.Element) -> Optional[PlacspLicitacion]:
        """
        Extract from CODICE ContractFolderStatus element.

        Args:
            contract_folder: ContractFolderStatus element
            entry_id: Entry ID
            entry_elem: Full entry element (for atom:title, atom:summary)

        Returns:
            PlacspLicitacion object
        """
        licitacion = PlacspLicitacion(
            identifier=entry_id,
            link="",
            update_date="",
        )

        # CODICE namespaces
        ns = {
            "basic": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
            "ext_basic": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2",
            "agg": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
            "ext_agg": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2",
            "atom": "http://www.w3.org/2005/Atom",
        }

        # Extract ID and status from ContractFolder
        contract_id = self._get_text_codice(contract_folder, f"{{{ns['basic']}}}ContractFolderID")
        if contract_id:
            licitacion.expedition_number = contract_id

        status_code = self._get_text_codice(contract_folder, f"{{{ns['ext_basic']}}}ContractFolderStatusCode")
        if status_code:
            licitacion.status = status_code

        # Get title from ATOM entry
        atom_title = entry_elem.find(f"{{{ns['atom']}}}title")
        if atom_title is not None and atom_title.text:
            licitacion.contract_object = atom_title.text.strip()

        # Get summary from ATOM entry
        atom_summary = entry_elem.find(f"{{{ns['atom']}}}summary")
        if atom_summary is not None and atom_summary.text:
            # Parse summary to extract key fields
            summary_text = atom_summary.text
            self._extract_from_summary(summary_text, licitacion)

        # Extract authority (LocatedContractingParty)
        contracting_party = contract_folder.find(f"{{{ns['ext_agg']}}}LocatedContractingParty")
        if contracting_party is not None:
            self._extract_authority_from_codice(contracting_party, licitacion, ns)

        # Extract procurement project details
        project = contract_folder.find(f"{{{ns['agg']}}}ProcurementProject")
        if project is not None:
            self._extract_project_from_codice(project, licitacion, ns)

        # Extract lots
        licitacion.lots = self._extract_lots_from_codice(contract_folder, ns)

        # Extract tendering process
        tendering = contract_folder.find(f"{{{ns['agg']}}}TenderingProcess")
        if tendering is not None:
            self._extract_tendering_from_codice(tendering, licitacion, ns)

        # Extract results/awards
        licitacion.results = self._extract_results_from_codice(contract_folder, ns)

        return licitacion

    def _extract_from_summary(self, summary_text: str, licitacion: PlacspLicitacion):
        """Extract key fields from summary text."""
        # Summary format: "Id licitación: X; Órgano de Contratación: Y; Importe: Z; Estado: W"
        parts = {}
        for part in summary_text.split(";"):
            if ":" in part:
                key, value = part.split(":", 1)
                parts[key.strip().lower()] = value.strip()

        if "id licitación" in parts:
            licitacion.expedition_number = parts["id licitación"]

        if "órgano de contratación" in parts:
            licitacion.contracting_authority = parts["órgano de contratación"]

        if "importe" in parts:
            amount_str = parts["importe"].split()[0]  # Remove "EUR" or other currency
            try:
                licitacion.budget_without_taxes = Decimal(amount_str.replace(".", "").replace(",", "."))
            except:
                pass

        if "estado" in parts:
            licitacion.status = parts["estado"]

    def _extract_authority_from_codice(self, party_elem: ET.Element, licitacion: PlacspLicitacion, ns: dict):
        """Extract authority information from CODICE structure."""
        party = party_elem.find(f"{{{ns['agg']}}}Party")
        if party is None:
            return

        licitacion.contracting_authority = self._get_text_codice(party, f"{{{ns['agg']}}}PartyName/{{{ns['basic']}}}Name")

        # Extract identifiers
        for id_elem in party.findall(f"{{{ns['agg']}}}PartyIdentification/{{{ns['basic']}}}ID"):
            scheme = id_elem.get("schemeName", "")
            if scheme == "DIR3":
                licitacion.authority_dir3 = id_elem.text
            elif scheme == "NIF":
                licitacion.authority_tax_id = id_elem.text

        # Extract contact
        contact = party.find(f"{{{ns['agg']}}}Contact")
        if contact is not None:
            phone = contact.find(f"{{{ns['basic']}}}Telephone")
            if phone is not None and phone.text:
                licitacion.authority_profile_link = phone.text  # Reuse field for contact info

    def _extract_project_from_codice(self, project_elem: ET.Element, licitacion: PlacspLicitacion, ns: dict):
        """Extract procurement project details from CODICE."""
        name = self._get_text_codice(project_elem, f"{{{ns['basic']}}}Name")
        if name:
            licitacion.contract_object = name

        # Type code
        type_code = project_elem.find(f"{{{ns['basic']}}}TypeCode")
        if type_code is not None:
            licitacion.contract_type = type_code.text

        # Budget
        budget = project_elem.find(f"{{{ns['agg']}}}BudgetAmount")
        if budget is not None:
            estimated = self._get_decimal_codice(budget, f"{{{ns['basic']}}}EstimatedOverallContractAmount")
            if estimated:
                licitacion.budget_without_taxes = estimated

            total = self._get_decimal_codice(budget, f"{{{ns['basic']}}}TotalAmount")
            if total:
                licitacion.budget_with_taxes = total

        # CPV
        cpv = project_elem.find(f"{{{ns['agg']}}}RequiredCommodityClassification/{{{ns['basic']}}}ItemClassificationCode")
        if cpv is not None and cpv.text:
            licitacion.cpv_code = cpv.text

        # Location
        location = project_elem.find(f"{{{ns['agg']}}}RealizedLocation")
        if location is not None:
            subentity = self._get_text_codice(location, f"{{{ns['basic']}}}CountrySubentity")
            if subentity:
                licitacion.execution_place_name = subentity

            code = location.find(f"{{{ns['basic']}}}CountrySubentityCode")
            if code is not None and code.text:
                licitacion.execution_place_nuts = code.text

    def _extract_lots_from_codice(self, contract_folder: ET.Element, ns: dict) -> list[ContractLot]:
        """Extract lots from CODICE structure."""
        lots = []
        for lot_elem in contract_folder.findall(f"{{{ns['agg']}}}ProcurementProjectLot"):
            lot = ContractLot()

            lot_id = lot_elem.find(f"{{{ns['basic']}}}ID")
            if lot_id is not None:
                lot.lot_number = lot_id.text

            project = lot_elem.find(f"{{{ns['agg']}}}ProcurementProject")
            if project is not None:
                lot.object = self._get_text_codice(project, f"{{{ns['basic']}}}Name")

                budget = project.find(f"{{{ns['agg']}}}BudgetAmount")
                if budget is not None:
                    lot.budget_without_taxes = self._get_decimal_codice(budget, f"{{{ns['basic']}}}TaxExclusiveAmount")
                    lot.budget_with_taxes = self._get_decimal_codice(budget, f"{{{ns['basic']}}}TotalAmount")

                cpv = project.find(f"{{{ns['agg']}}}RequiredCommodityClassification/{{{ns['basic']}}}ItemClassificationCode")
                if cpv is not None:
                    lot.cpv_code = cpv.text

            lots.append(lot)

        return lots

    def _extract_tendering_from_codice(self, tendering_elem: ET.Element, licitacion: PlacspLicitacion, ns: dict):
        """Extract tendering process details."""
        proc_code = tendering_elem.find(f"{{{ns['basic']}}}ProcedureCode")
        if proc_code is not None:
            licitacion.procedure_type = proc_code.text

        system_code = tendering_elem.find(f"{{{ns['basic']}}}ProcurementSystemCode")
        if system_code is not None:
            licitacion.system_type = system_code.text

    def _extract_results_from_codice(self, contract_folder: ET.Element, ns: dict) -> list[ContractResult]:
        """Extract results/awards from CODICE structure."""
        results = []
        for result_elem in contract_folder.findall(f"{{{ns['agg']}}}TenderResult"):
            result = ContractResult()

            code = result_elem.find(f"{{{ns['basic']}}}ResultCode")
            if code is not None:
                result.result_status = code.text

            award_date = result_elem.find(f"{{{ns['basic']}}}AwardDate")
            if award_date is not None:
                result.award_date = award_date.text

            result.awarded_companies = self._extract_awarded_from_codice(result_elem, ns)

            results.append(result)

        return results

    def _extract_awarded_from_codice(self, result_elem: ET.Element, ns: dict) -> list[AwardedCompany]:
        """Extract awarded companies from CODICE result."""
        companies = []
        for supplier_elem in result_elem.findall(f"{{{ns['ext_agg']}}}AwardedSupplier"):
            company = AwardedCompany()

            party = supplier_elem.find(f"{{{ns['agg']}}}SupplierParty/{{{ns['agg']}}}Party")
            if party is not None:
                company.name = self._get_text_codice(party, f"{{{ns['agg']}}}PartyName/{{{ns['basic']}}}Name")

                id_elem = party.find(f"{{{ns['agg']}}}PartyIdentification/{{{ns['basic']}}}ID")
                if id_elem is not None:
                    company.identifier = id_elem.text
                    company.identifier_type = id_elem.get("schemeName", "")

            sme = supplier_elem.find(f"{{{ns['basic']}}}SMEIndicator")
            if sme is not None and sme.text:
                company.is_pyme = sme.text.lower() in ["true", "1", "sí", "si"]

            amount = supplier_elem.find(f"{{{ns['agg']}}}AwardAmount/{{{ns['basic']}}}TaxExclusiveAmount")
            if amount is not None:
                try:
                    company.award_amount_without_taxes = Decimal(amount.text)
                except:
                    pass

            companies.append(company)

        return companies

    def _get_text_codice(self, elem: ET.Element, xpath: str) -> Optional[str]:
        """Get text using namespace-aware XPath."""
        try:
            found = elem.find(xpath)
            if found is not None and found.text:
                return found.text.strip()
        except:
            pass
        return None

    def _get_decimal_codice(self, elem: ET.Element, xpath: str) -> Optional[Decimal]:
        """Get decimal value from CODICE element."""
        try:
            found = elem.find(xpath)
            if found is not None and found.text:
                return Decimal(found.text.strip())
        except:
            pass
        return None

    def _extract_from_root(self, root: ET.Element, entry_id: str) -> Optional[PlacspLicitacion]:
        """
        Extract from parsed XML root element.

        Args:
            root: Root XML element
            entry_id: Entry ID

        Returns:
            PlacspLicitacion object
        """
        # Start with required fields
        licitacion = PlacspLicitacion(
            identifier=entry_id,
            link="",  # Will be populated from ATOM entry
            update_date="",  # Will be populated from ATOM entry
        )

        # Extract basic info
        licitacion.expedition_number = self._get_text(root, "pcsp:codigoExpediente")
        licitacion.contract_object = self._get_text(root, "pcsp:objetoContrato")
        licitacion.status = self._get_text(root, "pcsp:estado")
        licitacion.status_phase = self._get_text(root, "pcsp:fase")
        licitacion.first_publication_date = self._get_text(root, "pcsp:fechaPrimeraPublicacion")

        # Budget
        licitacion.estimated_value = self._get_decimal(root, "pcsp:valorEstimado")
        licitacion.budget_without_taxes = self._get_decimal(root, "pcsp:presupuestoSinImpuestos")
        licitacion.budget_with_taxes = self._get_decimal(root, "pcsp:presupuestoConImpuestos")

        # Contract type
        licitacion.contract_type = self._get_text(root, "pcsp:tipoContrato")
        licitacion.cpv_code = self._get_text(root, "pcsp:cpv")

        # Location
        licitacion.execution_place_nuts = self._get_text(root, "pcsp:lugarEjecucion/pcsp:codNUTS")
        licitacion.execution_place_name = self._get_text(root, "pcsp:lugarEjecucion/pcsp:denominacion")
        licitacion.postal_code = self._get_text(root, "pcsp:codigoPostal")

        # Contracting authority
        licitacion.contracting_authority = self._get_text(root, "pcsp:organoContratacion")
        licitacion.authority_id_placsp = self._get_text(root, "pcsp:idOCenPLACSP")
        licitacion.authority_tax_id = self._get_text(root, "pcsp:nifOC")
        licitacion.authority_dir3 = self._get_text(root, "pcsp:dir3OC")
        licitacion.authority_profile_link = self._get_text(root, "pcsp:enlacePerfilContratante")

        # Administration type
        licitacion.administration_type = self._get_text(root, "pcsp:tipoAdministracion")

        # Procedure
        licitacion.procedure_type = self._get_text(root, "pcsp:tipoConvocatoria")
        licitacion.system_type = self._get_text(root, "pcsp:sistemaContratacion")
        licitacion.processing_type = self._get_text(root, "pcsp:tramitacion")
        licitacion.offer_presentation_form = self._get_text(root, "pcsp:formaPresentacionOferta")
        licitacion.applicable_directive = self._get_text(root, "pcsp:directivaAplicable")

        # Subcontracting
        subcontracting_text = self._get_text(root, "pcsp:subcontratacionPermitida")
        if subcontracting_text:
            licitacion.subcontracting_allowed = subcontracting_text.lower() in ["sí", "true", "si"]

        licitacion.subcontracting_percentage = self._get_decimal(root, "pcsp:porcentajeSubcontratacion")

        # Extract lots
        licitacion.lots = self._extract_lots(root)

        # Extract results (awards)
        licitacion.results = self._extract_results(root)

        return licitacion

    def _extract_lots(self, root: ET.Element) -> list[ContractLot]:
        """Extract all lots from the licitacion."""
        lots = []

        # Find all lote elements
        for lote_elem in root.findall(".//pcsp:lote", self.NAMESPACES):
            lot = ContractLot()

            lot.lot_number = self._get_text(lote_elem, "pcsp:numeroLote")
            lot.object = self._get_text(lote_elem, "pcsp:objeto")
            lot.budget_without_taxes = self._get_decimal(lote_elem, "pcsp:presupuestoSinImpuestos")
            lot.budget_with_taxes = self._get_decimal(lote_elem, "pcsp:presupuestoConImpuestos")
            lot.cpv_code = self._get_text(lote_elem, "pcsp:cpv")
            lot.execution_place = self._get_text(lote_elem, "pcsp:lugarEjecucion")

            lots.append(lot)

        return lots

    def _extract_results(self, root: ET.Element) -> list[ContractResult]:
        """Extract all results/awards from the licitacion."""
        results = []

        # Find all resultado elements
        for resultado_elem in root.findall(".//pcsp:resultado", self.NAMESPACES):
            result = ContractResult()

            result.lot_number = self._get_text(resultado_elem, "pcsp:numeroLote")
            result.result_status = self._get_text(resultado_elem, "pcsp:estado")
            result.award_date = self._get_text(resultado_elem, "pcsp:fechaAdjudicacion")
            result.num_offers_received = self._get_int(resultado_elem, "pcsp:numeroOfertasRecibidas")
            result.lowest_offer_amount = self._get_decimal(resultado_elem, "pcsp:precioOfertaMasBaja")
            result.highest_offer_amount = self._get_decimal(resultado_elem, "pcsp:precioOfertaMasAlta")

            abnormally_low = self._get_text(resultado_elem, "pcsp:ofertasExcluidasAbnormementebajas")
            if abnormally_low:
                result.abnormally_low_offers_excluded = abnormally_low.lower() in ["sí", "true", "si"]

            result.contract_number = self._get_text(resultado_elem, "pcsp:numeroContrato")
            result.contract_formalization_date = self._get_text(
                resultado_elem, "pcsp:fechaFormalizacion"
            )
            result.contract_effective_date = self._get_text(resultado_elem, "pcsp:fechaEntradaVigor")

            # Extract awarded companies
            result.awarded_companies = self._extract_awarded_companies(resultado_elem)

            results.append(result)

        return results

    def _extract_awarded_companies(self, resultado_elem: ET.Element) -> list[AwardedCompany]:
        """Extract all awarded companies from a result element."""
        companies = []

        for adjudicatario_elem in resultado_elem.findall(".//pcsp:adjudicatario", self.NAMESPACES):
            company = AwardedCompany()

            company.name = self._get_text(adjudicatario_elem, "pcsp:denominacion")
            company.identifier_type = self._get_text(adjudicatario_elem, "pcsp:tipoIdentificador")
            company.identifier = self._get_text(adjudicatario_elem, "pcsp:identificador")

            is_pyme = self._get_text(adjudicatario_elem, "pcsp:esmenor")
            if is_pyme:
                company.is_pyme = is_pyme.lower() in ["sí", "true", "si"]

            company.award_amount_without_taxes = self._get_decimal(
                adjudicatario_elem, "pcsp:importeAdjudicacionSinImpuestos"
            )
            company.award_amount_with_taxes = self._get_decimal(
                adjudicatario_elem, "pcsp:importeAdjudicacionConImpuestos"
            )

            companies.append(company)

        return companies

    def _get_text(self, elem: ET.Element, xpath: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get text from element using XPath with namespaces.

        Args:
            elem: XML element
            xpath: XPath expression (with namespace prefixes)
            default: Default value if not found

        Returns:
            Text content or default
        """
        try:
            found = elem.find(xpath, self.NAMESPACES)
            if found is not None and found.text:
                return found.text.strip()
        except Exception as e:
            self.logger.debug(f"Error getting text from {xpath}: {e}")

        return default

    def _get_decimal(self, elem: ET.Element, xpath: str) -> Optional[Decimal]:
        """
        Get decimal value from element.

        Handles both Spanish (1.234,56) and English (1,234.56) number formats.

        Args:
            elem: XML element
            xpath: XPath expression

        Returns:
            Decimal value or None
        """
        text = self._get_text(elem, xpath)
        if not text:
            return None

        try:
            # Handle both Spanish (1.234,56) and English (1,234.56) formats
            cleaned = text.strip()

            # If there's both comma and dot, determine which is decimal separator
            if "," in cleaned and "." in cleaned:
                comma_pos = cleaned.rfind(",")
                dot_pos = cleaned.rfind(".")

                if comma_pos > dot_pos:
                    # Spanish format: 1.234,56 -> remove dots, replace comma with dot
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    # English format: 1,234.56 -> just remove commas
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                # Only comma - assume it's decimal separator (Spanish)
                cleaned = cleaned.replace(",", ".")

            # If only dots, leave as is (could be thousands or decimal)
            return Decimal(cleaned)
        except Exception as e:
            self.logger.debug(f"Failed to parse decimal {text}: {e}")
            return None

    def _get_int(self, elem: ET.Element, xpath: str) -> Optional[int]:
        """
        Get integer value from element.

        Args:
            elem: XML element
            xpath: XPath expression

        Returns:
            Integer value or None
        """
        text = self._get_text(elem, xpath)
        if not text:
            return None

        try:
            return int(text)
        except ValueError:
            self.logger.debug(f"Failed to parse integer {text}")
            return None