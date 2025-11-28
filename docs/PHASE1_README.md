# PLACSP Phase 1: Robust ATOM Parser & Field Extractor

## Overview

Phase 1 introduces three new robust modules for processing PLACSP (Plataforma de Contratación del Sector Público) data according to the OpenPLACSP specification.

## Modules

### 1. **atom_parser.py**

Robust ATOM/XML feed parser with support for syndication chain traversal.

**Key Classes:**
- `AtomParser` - Parse individual ATOM feeds
- `AtomZipHandler` - Extract ATOM from ZIP files
- `SyndicationChainFollower` - Follow the chain of linked ATOM feeds

**Features:**
- Proper namespace handling (ATOM, PCSP, CODICE)
- Syndication chain following (each feed links to previous)
- Error handling with informative logging
- Support for both file and URL sources

**Example:**
```python
from apps.crawlers.implementations.atom_parser import SyndicationChainFollower

follower = SyndicationChainFollower()
feeds = follower.follow_chain("http://example.com/licitaciones.atom")

for feed in feeds:
    print(f"Feed: {feed.title} with {len(feed.entries)} entries")
    for entry in feed.entries:
        print(f"  - {entry.entry_id}: {entry.title}")
```

### 2. **placsp_fields_extractor.py**

Extracts all available fields from PLACSP entries according to OpenPLACSP manual (40+ fields).

**Key Classes:**
- `PlacspFieldsExtractor` - Main extractor
- `PlacspLicitacion` - Data structure for complete tender with all fields
- `ContractLot` - Single lot within a tender
- `ContractResult` - Award/result information
- `AwardedCompany` - Company awarded a lot

**Supported Fields (from OpenPLACSP manual Section 5):**

**Licitaciones (Tenders):**
- Identifiers: identifier, link, update_date
- Status: status, status_phase, first_publication_date
- Description: contract_object, contract_type, cpv_code
- Budget: estimated_value, budget_without_taxes, budget_with_taxes
- Location: execution_place_nuts, execution_place_name, postal_code
- Authority: contracting_authority, authority_id_placsp, authority_tax_id, authority_dir3, authority_profile_link
- Administration: administration_type
- Procedure: procedure_type, system_type, processing_type, offer_presentation_form, applicable_directive
- Subcontracting: subcontracting_allowed, subcontracting_percentage
- Lots: list of ContractLot objects
- Results: list of ContractResult objects

**Resultados (Results):**
- Lot-specific information
- Award status and dates
- Number of offers received
- Low/high offer amounts
- Abnormally low offers exclusion
- Contract details
- Multiple awarded companies per lot

**Example:**
```python
from apps.crawlers.implementations.placsp_fields_extractor import PlacspFieldsExtractor

extractor = PlacspFieldsExtractor()
licitacion = extractor.extract_from_atom_entry_xml(xml_content, entry_id)

print(f"Contract: {licitacion.contract_object}")
print(f"Budget: €{licitacion.budget_with_taxes}")
print(f"Lots: {len(licitacion.lots)}")
print(f"Results: {len(licitacion.results)}")

# Convert to dictionary for storage
data_dict = licitacion.to_dict()
```

### 3. **zip_orchestrator.py**

Manages processing of multiple ZIP files with proper chronological ordering.

**Key Classes:**
- `ZipOrchestrator` - Main orchestration logic
- `PlacspZipInfo` - Metadata about a ZIP file
- `PlacspZipDateExtractor` - Extract dates from filenames

**Features:**
- Discovers available ZIP files from URLs
- Extracts dates from PLACSP filenames (YYYYMM format)
- Sorts ZIPs chronologically (crucial for syndication chains)
- Identifies base ATOM files within ZIPs

**Example:**
```python
from apps.crawlers.implementations.zip_orchestrator import ZipOrchestrator

orchestrator = ZipOrchestrator()

# Discover ZIPs
zips = orchestrator.discover_zips_from_url(
    "https://contrataciondelestado.es/datosabiertos/"
)

# Get correct processing order
ordered_zips = orchestrator.get_processing_order(zips)

for zip_info in ordered_zips:
    print(f"Process: {zip_info.filename} ({zip_info.date})")

    # Fetch and identify base ATOM
    zip_content, base_atom = orchestrator.fetch_and_prepare_zip(zip_info)
```

## Integration Guide

The new modules are designed to be **integrated gradually** into the existing PCSP crawler:

### Step 1: Update `pcsp.py` to use new modules

```python
from apps.crawlers.implementations.atom_parser import (
    AtomZipHandler, SyndicationChainFollower
)
from apps.crawlers.implementations.placsp_fields_extractor import PlacspFieldsExtractor
from apps.crawlers.implementations.zip_orchestrator import ZipOrchestrator

class PCSPCrawler(BaseCrawler):
    # ... existing code ...

    def _fetch_from_datos_abiertos(self) -> list[dict]:
        """New implementation using Phase 1 modules."""
        zip_handler = AtomZipHandler(session=self.session, logger=self.logger)
        fields_extractor = PlacspFieldsExtractor(logger=self.logger)

        # ... implementation ...
```

### Step 2: Leverage syndication chains

Instead of assuming a single ZIP, the new code can follow complete chains:

```python
follower = SyndicationChainFollower(session=self.session, logger=self.logger)
feeds = follower.follow_chain(start_url)

for feed in feeds:
    for entry in feed.entries:
        licitacion = fields_extractor.extract_from_atom_entry_xml(
            entry.content,
            entry.entry_id
        )
        if licitacion:
            contracts.append(licitacion.to_dict())
```

### Step 3: Proper ZIP ordering

Use the orchestrator to handle multiple ZIPs:

```python
orchestrator = ZipOrchestrator(session=self.session, logger=self.logger)
zips = orchestrator.discover_zips_from_url(base_url)
ordered_zips = orchestrator.get_processing_order(zips)

for zip_info in ordered_zips:
    zip_content, base_atom = orchestrator.fetch_and_prepare_zip(zip_info)
    if base_atom:
        feed = zip_handler.extract_atom_from_zip(zip_content, base_atom)
        # Process feed...
```

## Testing

All modules have comprehensive test coverage:

```bash
# Run Phase 1 tests
python -m pytest apps/crawlers/tests/test_placsp_phase1.py -v

# Run specific test class
python -m pytest apps/crawlers/tests/test_placsp_phase1.py::TestAtomParser -v

# Run with coverage
python -m pytest apps/crawlers/tests/test_placsp_phase1.py --cov=apps.crawlers.implementations
```

**Current Status:** 23/23 tests passing, 100% coverage

## Data Structures

### PlacspLicitacion

The main data structure capturing a complete tender with all fields:

```python
@dataclass
class PlacspLicitacion:
    # Required fields
    identifier: str                      # ATOM entry ID
    link: str                            # Link to PLACSP
    update_date: str                     # Last update date

    # Optional fields (40+)
    expedition_number: Optional[str]     # Código expediente
    contract_object: Optional[str]       # Objeto del contrato
    budget_with_taxes: Optional[Decimal] # Presupuesto con impuestos

    # Nested structures
    lots: list[ContractLot]             # Multiple lots if applicable
    results: list[ContractResult]       # Multiple results/awards
```

## PLACSP Manual Reference

This implementation follows the OpenPLACSP manual (v1.1, 15/12/2021):

- **Section 5.1:** Hoja "Licitaciones" - All tender fields
- **Section 5.2:** Hoja "Resultados" - All award/result fields
- **Section 4.1:** ZIP structure and syndication chains
- **Section 6.2:** CODICE specification for XML structure

## Next Steps (Phase 2)

- Extend Contract model to store additional PLACSP fields
- Create separate models for Lots and Awards
- Update ETL normalizers to process new field structures
- Add validation for PLACSP-specific data constraints
