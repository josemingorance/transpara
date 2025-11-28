# Quick Reference: PLACSP ATOM Data

## Your Question
**Q:** "siempre sale licitacion None pero yo veo datos, que pasa?"
**A:** Data is in raw_element, not in content field. ✅

---

## One-Line Answers

| Q | A |
|---|---|
| **Why is content=None?** | PLACSP doesn't use `atom:content`. Data is directly in entry children. |
| **Where is the data?** | In `entry.raw_element` as CODICE XML structure. |
| **Is it lost?** | No! All 40+ fields are there. |
| **Is this normal?** | Yes, this is CODICE standard (EU e-procurement). |
| **What can I extract?** | Everything: tender, authority, budget, lots, awards, companies. |
| **What do I do?** | Parse `raw_element` using CODICE XPath instead of reading `content`. |

---

## The Problem in Pictures

### What Happened
```
Crawler finds ZIP ✅
  ↓
Extracts ATOM ✅
  ↓
Parses entries ✅
  ↓
Checks entry.content ← Was None for all entries
  ↓
Returns None ❌
```

### Why It Failed
```
Code:           entry.content
Expected:       XML with procurement data
PLACSP reality: None (data is elsewhere)
Result:         Extraction failed
```

### Where Data Actually Is
```
entry.raw_element (XML tree)
├── atom:id ✅
├── atom:title ✅
├── atom:updated ✅
├── atom:summary ✅
│
└── ContractFolderStatus ← ALL 40+ FIELDS ARE HERE! ✅
    ├── ContractFolderID
    ├── ContractFolderStatusCode
    ├── LocatedContractingParty (authority)
    ├── ProcurementProject (tender details)
    ├── ProcurementProjectLot (lots)
    ├── TenderingProcess (procedure)
    ├── TenderResult (awards)
    └── AwardedSupplier (winners)
```

---

## What You Can Extract

### Core Fields (20+ fields)
```
Tender ID, Title, Description, Status, Type
CPV Code, Budget, Currency
Publication Date, Update Date
Authority Name, Authority Type, Authority ID, Contact
Execution Location, NUTS Code, Country
Procedure Type, Framework, E-auction
Subcontracting Allowed/Percentage
```

### Repeating Fields (Per Lot)
```
For each lot (1+):
  - Lot ID, Lot Description
  - Lot Budget, Lot CPV
  - Lot Execution Location
```

### Repeating Fields (Per Award)
```
For each award (1+):
  - Result Status, Award Date
  - Number of Offers, Min/Max Offer Amount
  - Contract Number, Formalization Date

For each company (1+):
  - Company Name, Company Type, Company ID
  - Is SME?, Award Amount
```

**Total: 40-50+ fields** ✅

---

## Real Example from PLACSP

From actual November 2024 data:

```
Entry ID: https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/14404712
Title: Suministro de munición 9 mm para diversas Unidades de la Guardia Civil

CODICE Data (in raw_element):
  ContractFolderID: R/0003/A/24/2
  Status: ADJ (Awarded)

  Authority:
    Name: Jefatura de Asuntos Económicos de la Guardia Civil
    DIR3: E04931401
    NIF: S2816003D
    Phone: 915142866
    Email: dg-contratacion-plm@guardiacivil.org
    Address: Calle Guzmán el Bueno 110, 28003 Madrid

  Budget: 6,840,000 EUR (without tax) / 8,276,400 EUR (with tax)

  Location: Madrid, NUTS: ES300

  Type: Supplies (CPV: 35331500)

  Lots:
    1. Cartuchería 9x19 mm PB NATO - 3,690,000 EUR
    2. Cartuchería 9x19 mm NO TOX - 1,350,000 EUR
```

✅ All of this is extractable!

---

## Namespaces Used

```
atom:    http://www.w3.org/2005/Atom
         → ATOM feed elements (id, title, etc.)

ns1:     urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2
         → CODICE extended aggregate components

ns2:     urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2
         → CODICE basic components (names, IDs, amounts)

ns3:     urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2
         → CODICE extended basic components

ns4:     urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2
         → CODICE aggregate components (parties, projects, etc.)
```

---

## Why This Format?

### Before (2021 Manual)
```xml
<atom:entry>
  <atom:content>
    <embedded-xml>...</embedded-xml>  ← String inside XML
  </atom:content>
</atom:entry>
```
❌ Pros: Simple
❌ Cons: Double parsing, inefficient

### Now (2024 PLACSP - CODICE)
```xml
<atom:entry>
  <ContractFolderStatus>  ← Structured directly
    ...all fields...
  </ContractFolderStatus>
</atom:entry>
```
✅ Pros: Clean, standard, efficient, direct access
✅ Cons: Need to know CODICE structure

---

## Timeline

| Year | What | Status |
|------|------|--------|
| 2021 | OpenPLACSP manual documents embedded content format | Published |
| 2023 | PLACSP evolves to CODICE standard | Migration |
| 2024 (now) | All feeds use CODICE structure | Current |

**Our code was based on 2021 format → needs update for 2024 format**

---

## The Solution

### ❌ Old Approach
```python
if entry.content:
    extract_from(entry.content)
else:
    return None  # FAIL
```

### ✅ New Approach
```python
if entry.raw_element:
    root = entry.raw_element
    contract_folder = root.find('ns1:ContractFolderStatus', namespaces)
    extract_from(contract_folder)  # SUCCESS
```

---

## Document Quick Links

| Document | Purpose | Read if... |
|----------|---------|-----------|
| **UNDERSTANDING_PLACSP_DATA.md** | Complete 100% explanation | You want full context |
| **ATOM_STRUCTURE_ANALYSIS.md** | Technical deep-dive | You're implementing |
| **DATA_AVAILABILITY_SUMMARY.md** | Field reference | You want to know what's available |
| **DEBUG_FINDINGS.md** | Why it failed | You want to understand the bug |
| **QUICK_REFERENCE.md** | This file | You want the TL;DR |

---

## TL;DR

✅ **Data is there**
✅ **All 40+ fields accessible**
✅ **Location: entry.raw_element**
✅ **Format: CODICE XML structure**
✅ **This is normal/standard**
✅ **Easy to extract once you know where to look**

---

## Next Step

Read: **UNDERSTANDING_PLACSP_DATA.md** (gives you the 100% picture)

Then: Check **ATOM_STRUCTURE_ANALYSIS.md** for implementation strategy

