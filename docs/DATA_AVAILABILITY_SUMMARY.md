# PLACSP Data Availability & Extraction Summary

## Quick Answer to Your Questions

### Q1: "Qué puedo sacar?" (What can I extract?)

**Answer: 40-50+ fields per tender including:**
- Complete tender metadata (ID, title, description, status)
- Full contracting authority details (name, type, location, contact, tax ID, DIR3)
- Budget information (estimated, total, with/without taxes)
- Execution location (NUTS codes, postal zones)
- Procurement procedure details (type, system, framework)
- CPV classifications (for main tender and each lot)
- Multiple lots with individual details
- Award/result information with awarded companies
- All dates and status information

### Q2: "Por qué no saco licitaciones?" (Why aren't licitaciones being extracted?)

**Answer: The data IS there, but in the CODICE/XML structure, not in `atom:content`**

The old code was looking for an `atom:content` element that doesn't exist in PLACSP feeds. The actual data is in:
- `ContractFolderStatus` element (main structure)
- Nested in CODICE hierarchies
- Stored in `raw_element` of the AtomEntry

**Solution: Extract from `entry.raw_element` using CODICE XPath instead of trying to find `entry.content`**

### Q3: "¿Que igual es normal?" (Is this normal?)

**Answer: Yes, 100% normal!**

This is how modern EU e-procurement platforms work (following CODICE standard). The 2021 manual was based on older format. Current PLACSP uses structured CODICE XML.

---

## Data Structure Map

```
ATOM Entry
│
├─ atom:id                    → Tender ID URL
├─ atom:title                 → Tender title (short)
├─ atom:updated               → Last update time
├─ atom:summary               → Quick summary text
│  └─ "Id licitación: ...; Órgano: ...; Importe: X EUR; Estado: Y"
│
└─ ContractFolderStatus       ← ALL THE DETAILED DATA IS HERE
   │
   ├─ ContractFolderID        → Tender reference number
   ├─ ContractFolderStatusCode → Status (ADJ, PUB, etc.)
   ├─ UUID                     → TED tracking ID
   │
   ├─ LocatedContractingParty → Authority information
   │  ├─ ContractingPartyTypeCode → Type (1=Central, 2=Regional, etc.)
   │  ├─ ActivityCode          → Main + secondary activities
   │  ├─ Party
   │  │  ├─ WebsiteURI        → Authority website
   │  │  ├─ PartyIdentification
   │  │  │  ├─ ID[DIR3]       → DIR3 code
   │  │  │  ├─ ID[NIF]        → Tax ID
   │  │  │  └─ ID[ID_PLATAFORMA] → Platform ID
   │  │  ├─ PartyName         → Authority name
   │  │  ├─ PostalAddress     → Full address
   │  │  │  ├─ CityName
   │  │  │  ├─ PostalZone     → Postal code
   │  │  │  ├─ AddressLine
   │  │  │  └─ Country
   │  │  └─ Contact           → Contact details
   │  │     ├─ Name
   │  │     ├─ Telephone
   │  │     ├─ Telefax
   │  │     └─ ElectronicMail
   │  └─ ParentLocatedParty   → Higher level authorities (recursive)
   │
   ├─ ProcurementProject → Main tender details
   │  ├─ Name              → Description
   │  ├─ TypeCode          → Type (1=Goods, 2=Services, 3=Works, etc.)
   │  ├─ SubTypeCode       → Subtype
   │  ├─ BudgetAmount
   │  │  ├─ EstimatedOverallContractAmount  → Budget without tax
   │  │  ├─ TotalAmount                      → Budget with tax
   │  │  └─ TaxExclusiveAmount               → Budget confirmed without tax
   │  ├─ RequiredCommodityClassification
   │  │  └─ ItemClassificationCode          → CPV code
   │  ├─ RealizedLocation
   │  │  ├─ CountrySubentity    → Region name
   │  │  ├─ CountrySubentityCode → NUTS code
   │  │  └─ Address → Country, coordinates
   │  └─ PlannedPeriod
   │     └─ DurationMeasure     → Duration (days)
   │
   ├─ ProcurementProjectLot (repeating per lot)
   │  ├─ ID              → Lot number
   │  └─ ProcurementProject
   │     ├─ Name         → Lot description
   │     ├─ BudgetAmount → Lot budget (with/without tax)
   │     ├─ RequiredCommodityClassification → CPV per lot
   │     └─ RealizedLocation → Execution place
   │
   ├─ TenderingProcess → Tendering details
   │  ├─ ProcedureCode  → Procedure type (open, restricted, negotiated, etc.)
   │  ├─ ProcurementSystemCode → System type
   │  ├─ ProcessDescription
   │  │  ├─ IsFrameworkAgreement
   │  │  ├─ DynamicPurchasingSystemInd
   │  │  ├─ ElectronicAuctionUsed
   │  │  └─ SubcontractingTerms
   │  │     ├─ SubcontractingAllowedIndicator
   │  │     └─ SubcontractingPercent
   │  └─ EstimatedDurationPeriod
   │
   └─ TenderResult (per lot, repeating)
      ├─ ResultCode           → Result status (ADJ=Awarded, DES=Abandoned, etc.)
      ├─ AwardDate            → Award date
      ├─ ReceivedTenderQuantity → Number of offers
      ├─ LowerTenderAmount     → Lowest bid amount
      ├─ HigherTenderAmount    → Highest bid amount
      ├─ AbnormallyLowBidsIndicator → Abnormally low offers excluded?
      ├─ ContractNumber        → Final contract number
      ├─ ContractFormalizationDate → Contract formalization date
      ├─ ContractFormalizedIndicator → Is contract formalized?
      │
      └─ AwardedSupplier (repeating per winner per lot)
         ├─ SupplierParty
         │  ├─ PartyIdentification
         │  │  ├─ ID[NIF]    → Company tax ID
         │  │  └─ ID[type]   → Other identifiers
         │  └─ PartyName     → Company name
         ├─ SMEIndicator     → Is SME?
         └─ AwardAmount
            ├─ TaxExclusiveAmount → Amount without tax
            └─ TotalAmount → Amount with tax
```

---

## What We Know From Real Data (Nov 2024)

From analyzing actual PLACSP feed (202411.zip):

### Tender Example
- **ID:** R/0003/A/24/2
- **Title:** Suministro de munición 9 mm para diversas Unidades de la Guardia Civil
- **Authority:** Jefatura de Asuntos Económicos de la Guardia Civil
- **Budget:** 6,840,000 EUR (tax-free) / 8,276,400 EUR (with tax)
- **Status:** ADJ (Adjudicated)
- **Type:** Supplies
- **CPV:** 35331500 (Ammunition)
- **Location:** Madrid (NUTS: ES300)
- **Contact:** 915142866, dg-contratacion-plm@guardiacivil.org

### Lots (in this tender)
1. **Cartuchería 9x19 mm PB NATO** - 3,690,000 EUR
2. **Cartuchería 9x19 mm NO TOX** - 1,350,000 EUR

### Results
- Winner: (In extended data)
- Award amount: (In extended data)
- Number of offers received: (In extended data)

---

## Field Categories Available

### ✅ Tender Identification (5 fields)
- Tender ID
- Tender title/description
- Status
- Publication date
- Last update date

### ✅ Authority Information (10 fields)
- Authority name
- Authority type
- Tax ID (NIF)
- DIR3 code
- Platform ID
- Website
- Address (street, city, postal code)
- Contact phone/fax/email
- Parent authorities (recursive)

### ✅ Budget Information (6 fields)
- Estimated budget (without tax)
- Estimated budget (with tax)
- Total budget (without tax)
- Total budget (with tax)
- Currency (EUR)
- Budget clarification notes

### ✅ Tender Details (8 fields)
- Contract type (goods, services, works, mixed)
- Sub-type
- CPV classification
- Duration
- Execution location
- NUTS code
- Country
- Tender description

### ✅ Procedure Information (6 fields)
- Procedure type (open, restricted, negotiated, etc.)
- System type (traditional, dynamic purchasing, etc.)
- Framework agreement indicator
- Dynamic purchasing system indicator
- Electronic auction used
- Applicable directive (2014/24/EU, etc.)

### ✅ Subcontracting (2 fields)
- Subcontracting allowed (yes/no)
- Subcontracting percentage (if allowed)

### ✅ Lot Information (Per Lot: 5 fields)
- Lot number
- Lot description
- Lot budget (without tax)
- Lot budget (with tax)
- CPV per lot
- Execution location per lot

### ✅ Result Information (9 fields)
- Result status
- Award date
- Number of offers received
- Lowest offer amount
- Highest offer amount
- Abnormally low bids excluded (yes/no)
- Final contract number
- Contract formalization date
- Contract effective date

### ✅ Award Information (Per Award: 5 fields)
- Company name
- Company identifier type
- Company identifier value
- Is SME (yes/no)
- Award amount (without tax)
- Award amount (with tax)

---

## Summary Table

| Category | Fields | Available | Location |
|----------|--------|-----------|----------|
| Tender ID/Title | 3 | ✅ All | atom:title, atom:id, ContractFolderID |
| Dates | 5 | ✅ All | atom:updated, ProcurementProject dates |
| Authority | 10 | ✅ All | LocatedContractingParty |
| Budget | 6 | ✅ All | BudgetAmount |
| Tender Details | 8 | ✅ All | ProcurementProject |
| Procedure | 6 | ✅ All | TenderingProcess |
| Subcontracting | 2 | ✅ All | ProcessDescription |
| Lots | 5 per lot | ✅ All | ProcurementProjectLot |
| Results | 9 | ✅ All | TenderResult |
| Awards | 5 per award | ✅ All | AwardedSupplier |

**Total: 40-50+ fields depending on number of lots and awards**

---

## Extractable in Phase 1

✅ **Easy (field values):** 30+ fields
- IDs, names, dates, codes, amounts
- All simple text/number fields

✅ **Medium (structured):** 15+ fields
- Authority hierarchy
- Multiple lots
- Multiple award results
- Nested addresses/contacts

**All of these are in the CODICE structure and extractable!**

---

## Why This Will Work

1. **Data is structured** - CODICE XML is well-defined
2. **Namespace-aware** - Can use proper XPath with namespaces
3. **Repeating elements** - Can handle multiple lots/awards
4. **Standardized** - Same structure across all PLACSP entries
5. **Complete** - All necessary data is present

---

## Next: Implementation

To extract all 40+ fields:

1. **Read from `entry.raw_element`** instead of `entry.content`
2. **Use CODICE namespaces** in XPath queries
3. **Navigate hierarchy:** ContractFolderStatus → LocatedContractingParty → Party
4. **Handle repeating elements:** ProcurementProjectLot, TenderResult, AwardedSupplier
5. **Parse budget amounts** handling both formats
6. **Extract all standard CODICE fields**

This is **definitely doable and all data is available!**

