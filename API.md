## 🎯 PublicWorks AI - REST API Documentation

Complete API reference for the PublicWorks AI platform.

**Base URL**: `http://localhost:8000/api/v1/`

**Format**: JSON

**Authentication**: None (add JWT/Token auth in production)

---

## 📑 Table of Contents

1. [Contracts API](#contracts-api)
2. [Providers API](#providers-api)
3. [Analytics API](#analytics-api)
4. [Pagination & Filtering](#pagination--filtering)
5. [Error Responses](#error-responses)

---

## 🔷 Contracts API

### List Contracts

```http
GET /api/v1/contracts/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title, external_id, authority, description |
| `contract_type` | enum | WORKS, SERVICES, SUPPLIES, MIXED, OTHER |
| `status` | enum | DRAFT, PUBLISHED, IN_PROGRESS, AWARDED, COMPLETED, CANCELLED |
| `region` | string | Filter by region |
| `province` | string | Filter by province |
| `source_platform` | string | Filter by source (PCSP, BOE, etc.) |
| `budget_min` | number | Minimum budget |
| `budget_max` | number | Maximum budget |
| `risk_score_min` | number | Minimum risk score (0-100) |
| `risk_score_max` | number | Maximum risk score (0-100) |
| `publication_date_after` | date | After this date (YYYY-MM-DD) |
| `publication_date_before` | date | Before this date (YYYY-MM-DD) |
| `is_overpriced` | boolean | Only overpriced contracts |
| `has_amendments` | boolean | Only contracts with amendments |
| `has_delays` | boolean | Only contracts with delays |
| `high_risk` | boolean | Only high-risk contracts (score > 70) |
| `ordering` | string | Sort by: `publication_date`, `budget`, `risk_score`, `-budget` (desc) |
| `page` | number | Page number |
| `page_size` | number | Items per page (max 100) |

**Response:**
```json
{
  "count": 1523,
  "next": "http://localhost:8000/api/v1/contracts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "external_id": "PCSP-12345",
      "title": "Obra de construcción de infraestructura",
      "contract_type": "WORKS",
      "status": "AWARDED",
      "budget": "1234567.89",
      "awarded_amount": "1200000.00",
      "overpricing_percentage": "-2.81",
      "risk_score": "68.50",
      "is_overpriced": false,
      "publication_date": "2024-01-15",
      "deadline_date": "2024-02-15",
      "award_date": "2024-03-01",
      "contracting_authority": "Ayuntamiento de Madrid",
      "awarded_to": {
        "id": 42,
        "name": "Construcciones ABC S.L.",
        "tax_id": "B12345678",
        "risk_score": "45.20"
      },
      "region": "Madrid",
      "province": "Madrid",
      "municipality": "Madrid",
      "source_platform": "PCSP"
    }
  ]
}
```

### Get Contract Detail

```http
GET /api/v1/contracts/{id}/
```

**Response:**
```json
{
  "id": 1,
  "external_id": "PCSP-12345",
  "title": "Obra de construcción de infraestructura",
  "description": "Detailed description...",
  "contract_type": "WORKS",
  "status": "AWARDED",
  "budget": "1234567.89",
  "awarded_amount": "1200000.00",
  "overpricing_percentage": "-2.81",
  "procedure_type": "OPEN",
  "publication_date": "2024-01-15",
  "deadline_date": "2024-02-15",
  "award_date": "2024-03-01",
  "contracting_authority": "Ayuntamiento de Madrid",
  "awarded_to": {...},
  "region": "Madrid",
  "province": "Madrid",
  "municipality": "Madrid",
  "source_url": "https://contrataciondelestado.es/...",
  "source_platform": "PCSP",
  "risk_score": "68.50",
  "corruption_risk": "72.00",
  "delay_risk": "45.00",
  "financial_risk": "30.00",
  "has_high_risk": false,
  "is_overpriced": false,
  "has_amendments": true,
  "has_delays": false,
  "analyzed_at": "2024-01-20T10:30:00Z",
  "analysis_version": "1.0",
  "amendments": [
    {
      "id": 1,
      "amendment_type": "BUDGET_INCREASE",
      "description": "Aumento presupuestario",
      "previous_amount": "1234567.89",
      "new_amount": "1300000.00",
      "amount_change_percentage": "5.30",
      "amendment_date": "2024-03-15",
      "reason": "Costes adicionales",
      "created_at": "2024-03-16T08:00:00Z"
    }
  ],
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-20T10:30:00Z"
}
```

### Get Contract Statistics

```http
GET /api/v1/contracts/stats/
```

Supports same filters as list endpoint.

**Response:**
```json
{
  "total_contracts": 1523,
  "total_budget": "1234567890.00",
  "avg_budget": "810523.45",
  "high_risk_count": 142,
  "overpriced_count": 89,
  "avg_risk_score": "42.35"
}
```

### Get Contract Amendments

```http
GET /api/v1/contracts/{id}/amendments/
```

**Response:**
```json
[
  {
    "id": 1,
    "amendment_type": "BUDGET_INCREASE",
    "description": "Aumento presupuestario",
    "previous_amount": "1000000.00",
    "new_amount": "1100000.00",
    "amount_change_percentage": "10.00",
    "amendment_date": "2024-03-15",
    "reason": "Costes adicionales",
    "created_at": "2024-03-16T08:00:00Z"
  }
]
```

### Analyze Contract (Trigger AI)

```http
POST /api/v1/contracts/{id}/analyze/
```

**Response:**
```json
{
  "overpricing": {
    "score": 75.5,
    "model": "overpricing_detector",
    "explanation": "Contract is 45% above regional average",
    "factors": [...]
  },
  "corruption": {
    "score": 68.0,
    "model": "corruption_risk_scorer",
    "explanation": "Multiple red flags detected",
    "factors": [...]
  },
  "delay": {
    "score": 55.0,
    "model": "delay_predictor",
    "explanation": "Moderate delay risk",
    "factors": [...]
  },
  "financial": {
    "score": 30.0,
    "explanation": "Moderate financial risk",
    "factors": [...]
  },
  "overall": {
    "score": 68.8,
    "level": "HIGH",
    "explanation": "High risk level - detailed review recommended"
  }
}
```

### Group by Region

```http
GET /api/v1/contracts/by_region/
```

**Response:**
```json
[
  {
    "region": "Madrid",
    "count": 452,
    "total_budget": "450000000.00",
    "avg_risk_score": "45.20",
    "high_risk_count": 42
  }
]
```

### Group by Type

```http
GET /api/v1/contracts/by_type/
```

**Response:**
```json
[
  {
    "contract_type": "SERVICES",
    "count": 856,
    "total_budget": "650000000.00",
    "avg_risk_score": "42.10"
  }
]
```

---

## 🔷 Providers API

### List Providers

```http
GET /api/v1/providers/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in name, tax_id, legal_name |
| `region` | string | Filter by region |
| `industry` | string | Filter by industry |
| `total_contracts_min` | number | Minimum contract count |
| `total_contracts_max` | number | Maximum contract count |
| `risk_score_min` | number | Minimum risk score |
| `risk_score_max` | number | Maximum risk score |
| `is_flagged` | boolean | Only flagged providers |
| `high_risk` | boolean | Only high-risk (score > 70) |
| `ordering` | string | Sort by: `total_contracts`, `total_awarded_amount`, `risk_score` |

**Response:**
```json
{
  "count": 345,
  "results": [
    {
      "id": 42,
      "name": "Construcciones ABC S.L.",
      "tax_id": "B12345678",
      "region": "Madrid",
      "industry": "Construction",
      "total_contracts": 45,
      "total_awarded_amount": "15000000.00",
      "avg_contract_amount": "333333.33",
      "success_rate": "45.50",
      "risk_score": "35.20",
      "is_flagged": false,
      "years_active": 5,
      "last_contract_date": "2024-01-15"
    }
  ]
}
```

### Get Provider Detail

```http
GET /api/v1/providers/{id}/
```

**Response:**
```json
{
  "id": 42,
  "name": "Construcciones ABC S.L.",
  "tax_id": "B12345678",
  "legal_name": "Construcciones ABC Sociedad Limitada",
  "address": "Calle Mayor 123",
  "city": "Madrid",
  "region": "Madrid",
  "postal_code": "28001",
  "phone": "+34 91 123 4567",
  "email": "info@abc.es",
  "website": "https://www.abc.es",
  "industry": "Construction",
  "company_size": "SME",
  "founded_year": 2015,
  "total_contracts": 45,
  "total_awarded_amount": "15000000.00",
  "avg_contract_amount": "333333.33",
  "success_rate": "45.50",
  "years_active": 5,
  "first_contract_date": "2019-03-10",
  "last_contract_date": "2024-01-15",
  "risk_score": "35.20",
  "has_high_risk": false,
  "is_flagged": false,
  "flag_reason": "",
  "created_at": "2019-03-10T10:00:00Z",
  "updated_at": "2024-01-20T14:30:00Z"
}
```

### Get Provider's Contracts

```http
GET /api/v1/providers/{id}/contracts/
```

Returns paginated list of contracts awarded to this provider.

### Get Provider's Alerts

```http
GET /api/v1/providers/{id}/alerts/
```

**Response:**
```json
[
  {
    "id": 123,
    "provider": 42,
    "provider_name": "Construcciones ABC S.L.",
    "provider_tax_id": "B12345678",
    "severity": "HIGH",
    "alert_type": "OVERPRICING",
    "title": "Overpricing detected in contract PCSP-12345",
    "description": "Contract price is 45% above market rates",
    "evidence": {
      "contract_id": "PCSP-12345",
      "overpricing_score": 82.5,
      "factors": [...]
    },
    "is_resolved": false,
    "resolved_at": null,
    "resolution_notes": "",
    "created_at": "2024-01-20T10:35:00Z",
    "updated_at": "2024-01-20T10:35:00Z"
  }
]
```

### Get Provider's Relationships

```http
GET /api/v1/providers/{id}/relationships/
```

**Response:**
```json
[
  {
    "id": 1,
    "provider_a": 42,
    "provider_a_name": "Construcciones ABC S.L.",
    "provider_b": 58,
    "provider_b_name": "Servicios XYZ S.L.",
    "relationship_type": "SHARED_ADDRESS",
    "confidence": "85.50",
    "evidence": {
      "addresses": ["Calle Mayor 123, Madrid"],
      "contracts_overlap": 12
    },
    "created_at": "2024-01-18T12:00:00Z"
  }
]
```

### Analyze Provider (Trigger AI)

```http
POST /api/v1/providers/{id}/analyze/
```

**Response:**
```json
{
  "score": 72.5,
  "model": "provider_analyzer",
  "explanation": "Provider shows multiple risk indicators",
  "factors": [
    {
      "factor": "Limited Experience",
      "score": 25.0,
      "description": "0.5 years experience but €2,500,000 in contracts",
      "risk_level": "high"
    },
    {
      "factor": "High Win Rate",
      "score": 20.0,
      "description": "90% success rate is suspiciously high",
      "risk_level": "high"
    }
  ]
}
```

### Provider Statistics

```http
GET /api/v1/providers/stats/
```

**Response:**
```json
{
  "total_providers": 345,
  "total_contracts": 1523,
  "total_awarded": "1234567890.00",
  "flagged_count": 28,
  "high_risk_count": 15,
  "avg_success_rate": "38.45"
}
```

### Group Providers by Region

```http
GET /api/v1/providers/by_region/
```

### Group Providers by Industry

```http
GET /api/v1/providers/by_industry/
```

---

## 🔷 Analytics API

### Dashboard Statistics

```http
GET /api/v1/analytics/dashboard/
```

**Response:**
```json
{
  "total_contracts": 1523,
  "total_budget": "1234567890.00",
  "high_risk_contracts": 142,
  "overpriced_contracts": 89,
  "total_providers": 345,
  "flagged_providers": 28,
  "avg_risk_score": "42.35",
  "critical_alerts": 12,
  "contracts_last_30_days": 89,
  "analyzed_last_24_hours": 45
}
```

### Regional Statistics

```http
GET /api/v1/analytics/regional_stats/
```

**Response:**
```json
[
  {
    "region": "Madrid",
    "total_contracts": 452,
    "total_budget": "450000000.00",
    "avg_risk_score": "45.20",
    "high_risk_count": 42,
    "overpriced_count": 28
  }
]
```

### Trends Over Time

```http
GET /api/v1/analytics/trends/?days=90
```

**Parameters:**
- `days`: Number of days to look back (default: 90)

**Response:**
```json
[
  {
    "date": "2024-01-15",
    "count": 12,
    "total_amount": "5000000.00",
    "avg_risk_score": "42.30"
  },
  {
    "date": "2024-01-16",
    "count": 8,
    "total_amount": "3200000.00",
    "avg_risk_score": "38.50"
  }
]
```

### Contract Type Distribution

```http
GET /api/v1/analytics/contract_type_distribution/
```

**Response:**
```json
[
  {
    "contract_type": "SERVICES",
    "count": 856,
    "total_budget": "650000000.00",
    "avg_risk_score": "42.10"
  }
]
```

### Top Providers

```http
GET /api/v1/analytics/top_providers/?by=amount&limit=10
```

**Parameters:**
- `by`: Sort by `contracts` or `amount` (default: contracts)
- `limit`: Number of providers (default: 10)

**Response:**
```json
[
  {
    "provider_id": 42,
    "provider_name": "Construcciones ABC S.L.",
    "provider_tax_id": "B12345678",
    "total_contracts": 45,
    "total_amount": "15000000.00",
    "risk_score": "35.20"
  }
]
```

### Risk Distribution

```http
GET /api/v1/analytics/risk_distribution/
```

**Response:**
```json
{
  "minimal": 245,
  "low": 412,
  "medium": 523,
  "high": 231,
  "critical": 112
}
```

### Alerts Summary

```http
GET /api/v1/analytics/alerts_summary/
```

**Response:**
```json
{
  "by_severity": [
    {"severity": "CRITICAL", "count": 12},
    {"severity": "HIGH", "count": 45},
    {"severity": "MEDIUM", "count": 78}
  ],
  "by_type": [
    {"alert_type": "OVERPRICING", "count": 42},
    {"alert_type": "CORRUPTION_INDICATORS", "count": 35}
  ],
  "total_unresolved": 135
}
```

### Recent High-Risk Contracts

```http
GET /api/v1/analytics/recent_high_risk/
```

Returns top 20 high-risk contracts from last 30 days.

---

## 🔧 Pagination & Filtering

### Pagination

All list endpoints support pagination:

```http
GET /api/v1/contracts/?page=2&page_size=50
```

**Response includes:**
- `count`: Total number of items
- `next`: URL to next page
- `previous`: URL to previous page
- `results`: Array of items

### Filtering

Combine multiple filters:

```http
GET /api/v1/contracts/?region=Madrid&risk_score_min=70&is_overpriced=true
```

### Ordering

Sort by any orderable field:

```http
GET /api/v1/contracts/?ordering=-risk_score
```

Use `-` prefix for descending order.

### Search

Full-text search:

```http
GET /api/v1/contracts/?search=construcción
```

---

## ⚠️ Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid filter parameter"
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error

```json
{
  "error": "An unexpected error occurred"
}
```

---

## 📊 API Usage Examples

### Find All High-Risk Contracts in Madrid

```bash
curl "http://localhost:8000/api/v1/contracts/?region=Madrid&high_risk=true"
```

### Get Flagged Providers with Relationships

```bash
# 1. Get flagged providers
curl "http://localhost:8000/api/v1/providers/?is_flagged=true"

# 2. Get relationships for provider #42
curl "http://localhost:8000/api/v1/providers/42/relationships/"
```

### Dashboard Data for Frontend

```bash
# Get all dashboard stats
curl "http://localhost:8000/api/v1/analytics/dashboard/"

# Get trends for charts
curl "http://localhost:8000/api/v1/analytics/trends/?days=30"

# Get regional distribution
curl "http://localhost:8000/api/v1/analytics/regional_stats/"
```

---

## 📝 Notes

- All dates are in ISO 8601 format (`YYYY-MM-DD`)
- All monetary amounts are strings (to preserve precision)
- Risk scores are 0-100 (decimal with 2 places)
- Timestamps are in UTC with timezone info

---

**API Documentation Version:** 1.0
**Last Updated:** 2024-01-20
**API Status:** ✅ Production Ready
