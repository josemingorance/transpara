# PLACSP ATOM Structure Analysis

## Discovery

**Date:** 2025-11-27
**Issue:** ATOM entries had `content=None`, making it impossible to extract 40+ fields
**Root Cause Found:** The CODICE/PCSP XML data is NOT in the `atom:content` element - it's directly in the ATOM entry as child elements!

---

## Actual ATOM Entry Structure

### Key Finding

The PLACSP syndication feeds use **CODICE eInvoicing standard** with extended PCSP namespaces. Each ATOM entry contains:

```
<atom:entry>
  <!-- ATOM metadata -->
  <atom:id>...</atom:id>
  <atom:title>...</atom:title>
  <atom:updated>...</atom:updated>
  <atom:link href="..."/>
  <atom:summary>...</atom:summary>

  <!-- CODICE/PCSP XML data DIRECTLY as children (NOT in atom:content!) -->
  <ns1:ContractFolderStatus>
    ...all the 40+ fields are here...
  </ns1:ContractFolderStatus>
</atom:entry>
```

### Namespaces Used

| Namespace | URL | Purpose |
|-----------|-----|---------|
| atom | http://www.w3.org/2005/Atom | ATOM feed format |
| ns1 | urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2 | CODICE extended aggregates |
| ns2 | urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2 | CODICE basic components |
| ns3 | urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2 | CODICE extended basics |
| ns4 | urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2 | CODICE aggregates |

---

## Available Data in Entry

### ATOM Metadata (Always present)
- `atom:id` - Unique identifier URL
- `atom:title` - Tender title
- `atom:updated` - Last update timestamp
- `atom:link[@href]` - Direct link to tender detail page
- `atom:summary` - Brief summary with key info (id, authority, amount, status)

### CODICE Elements (ContractFolderStatus structure)

**Main Contract Information:**
- `ContractFolderID` - Tender identifier (e.g., "R/0003/A/24/2")
- `ContractFolderStatusCode` - Status (ADJ=Adjudicated, etc.)
- `UUID` - TED UUID for tracking

**Contracting Authority:**
- `LocatedContractingParty` - Complete party information
  - Party type, activity codes
  - Party identification (DIR3, NIF, Platform ID)
  - Party name, website
  - Contact info, postal address

**Procurement Details:**
- `ProcurementProject` - Main tender information
  - Name, type, subtype
  - Budget amount (estimated, total, tax-exclusive)
  - CPV classification
  - Location (NUTS code, address)
  - Duration

**Lots:**
- `ProcurementProjectLot` (repeating for each lot)
  - Lot ID
  - Lot name
  - Budget (tax inclusive/exclusive)
  - CPV codes
  - Execution location

**Results/Awards:**
- `TenderingProcess` - Tendering details
  - Procedure type
  - System type
  - Framework agreements

- `TenderResult` - Award information (per lot)
  - Winner name, type, identifier
  - Award amount
  - Number of offers

---

## Why Previous Approach Failed

The old code expected:
```python
if entry.content:
    extract from entry.content
else:
    return None  # FAIL!
```

But actual PLACSP feeds have:
- **NO `atom:content` element** ❌
- **Direct CODICE XML elements** as entry children ✅

---

## Data Available Summary

### What We CAN Extract

✅ **Tender Metadata:** ID, title, description, status, dates
✅ **Budget:** Estimated, total, tax info
✅ **Authority:** Name, type, location, contact, DIR3, NIF
✅ **Location:** NUTS codes, postal zones, country
✅ **Procedure:** Type, system, framework, directive
✅ **CPV Codes:** For tender and lots
✅ **Lots:** Multiple lots with individual budgets and CPV
✅ **Awards:** Winner info, amounts, number of offers

### Estimated Field Count

- **Core Tender Fields:** 15-20
- **Authority Fields:** 8-10
- **Budget Fields:** 5-6
- **Location Fields:** 5-6
- **Procedure Fields:** 6-8
- **Per Lot Fields:** 5 × (number of lots)
- **Per Award Fields:** 6 × (number of awards)

**Total: 40-50+ fields depending on lots/awards**

---

## Raw XML Structure Example

```xml
<ns0:entry xmlns:ns0="http://www.w3.org/2005/Atom"
          xmlns:ns1="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2"
          xmlns:ns2="urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2"
          xmlns:ns3="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2"
          xmlns:ns4="urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2">

  <ns0:id>https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/14404712</ns0:id>

  <ns0:link href="https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=Y%2FmxRnknWXSsNfRW6APEDw%3D%3D" />

  <ns0:summary type="text">
    Id licitación: R/0003/A/24/2; Órgano de Contratación: Jefatura de Asuntos Económicos de la Guardia Civil;
    Importe: 6840000 EUR; Estado: ADJ
  </ns0:summary>

  <ns0:title>Suministro de munición 9 mm para diversas Unidades de la Guardia Civil.</ns0:title>

  <ns0:updated>2024-11-28T17:57:44.702+01:00</ns0:updated>

  <!-- CODICE structure - THIS is where the data is! -->
  <ns1:ContractFolderStatus>
    <ns2:ContractFolderID>R/0003/A/24/2</ns2:ContractFolderID>
    <ns3:ContractFolderStatusCode listURI="...">ADJ</ns3:ContractFolderStatusCode>

    <ns1:LocatedContractingParty>
      <ns2:ContractingPartyTypeCode>1</ns2:ContractingPartyTypeCode>
      <!-- Authority details... -->
    </ns1:LocatedContractingParty>

    <ns4:ProcurementProject>
      <ns2:Name>Suministro de munición 9 mm para diversas Unidades de la Guardia Civil.</ns2:Name>
      <ns2:TypeCode>1</ns2:TypeCode>
      <ns4:BudgetAmount>
        <ns2:EstimatedOverallContractAmount currencyID="EUR">6840000</ns2:EstimatedOverallContractAmount>
        <ns2:TaxExclusiveAmount currencyID="EUR">6840000</ns2:TaxExclusiveAmount>
      </ns4:BudgetAmount>
      <!-- More details... -->
    </ns4:ProcurementProject>

    <ns4:ProcurementProjectLot>
      <ns2:ID schemeName="ID_LOTE">1</ns2:ID>
      <!-- Lot details... -->
    </ns4:ProcurementProjectLot>

    <!-- More lots, award results, etc. -->
  </ns1:ContractFolderStatus>
</ns0:entry>
```

---

## Implementation Strategy

### Change 1: Update AtomParser

**Current behavior:**
- Looks for `atom:content` element
- Returns None if not found

**New behavior:**
- Check if `atom:content` exists (for compatibility)
- **If not:** Extract CODICE XML from entry children directly
- Store raw entry element in AtomEntry for extraction

### Change 2: Update PlacspFieldsExtractor

**Current behavior:**
- Expects XML string in `entry.content`
- Fails if content is None

**New behavior:**
- Accept either:
  1. XML string (legacy compatibility)
  2. ET.Element (raw entry element from AtomEntry.raw_element)
- Extract from ContractFolderStatus and nested elements

### Change 3: Update pcsp.py

**Current behavior:**
```python
if not entry.content:
    return None  # Skip entry
```

**New behavior:**
```python
# Try content first (for compatibility)
if entry.content:
    licitacion = extract_from_xml_string(entry.content)
else:
    # Use raw element (CODICE structure)
    licitacion = extract_from_raw_element(entry.raw_element)
```

---

## Why This is Actually Better

1. **More Direct:** Data is native CODICE, not embedded XML
2. **No Double Parsing:** Don't need to parse XML within XML
3. **Better Access:** Can use direct XPath to CODICE elements
4. **More Stable:** CODICE is standardized format
5. **Consistent:** All entries follow same CODICE structure

---

## Next Steps

1. ✅ Understand ATOM structure (DONE - you wanted to understand 100%)
2. Update atom_parser.py to extract CODICE elements
3. Update placsp_fields_extractor.py for CODICE mapping
4. Update pcsp.py to use raw_element extraction
5. Test with real PLACSP data
6. Verify all 40+ fields are extracted

---

## Conclusion

**The data is NOT missing - it's just in a different place than expected!**

PLACSP Sindication feeds contain complete CODICE/PCSP structured data directly in ATOM entries. The extraction needs to look at:
- Direct child elements of the entry (not atom:content)
- Specifically: ContractFolderStatus and its nested structure
- Use proper CODICE namespace-aware XPath queries

This is actually a **more robust and cleaner approach** than trying to parse embedded XML strings.

