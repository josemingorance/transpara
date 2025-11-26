#!/bin/bash

# Data Pipeline Orchestration Script
# Executes: crawl → normalize → analyze → report

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get Python and Django paths - use venv directly if available
VENV_PATH=".venv"
PARENT_VENV_PATH="../.venv"

if [ -d "$VENV_PATH" ]; then
    PYTHON_BIN="$VENV_PATH/bin/python"
    PYTHON_CMD="$PYTHON_BIN manage.py"
elif [ -d "$PARENT_VENV_PATH" ]; then
    PYTHON_BIN="$PARENT_VENV_PATH/bin/python"
    PYTHON_CMD="$PYTHON_BIN manage.py"
else
    PYTHON_CMD="python manage.py"
fi

# ==================== FUNCTIONS ====================

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# ==================== STEP 1: CRAWL ====================

crawl() {
    print_header "STEP 1: Running Crawlers"

    if $PYTHON_CMD run_crawlers; then
        print_success "Crawlers completed"
    else
        print_error "Crawlers failed"
        exit 1
    fi
}

# ==================== STEP 2: NORMALIZE ====================

normalize() {
    print_header "STEP 2: Normalizing Raw Data"

    if $PYTHON_CMD process_raw_data; then
        print_success "Normalization completed"
    else
        print_error "Normalization failed"
        exit 1
    fi
}

# ==================== STEP 3: ANALYZE ====================

analyze() {
    print_header "STEP 3: Running Risk Analysis"

    if $PYTHON_CMD analyze_risk --contracts; then
        print_success "Risk analysis completed"
    else
        print_error "Risk analysis failed"
        exit 1
    fi
}

# ==================== STEP 4: REPORT ====================

report() {
    print_header "STEP 4: Generating Report"

    $PYTHON_CMD shell << 'PYTHON_EOF'
from apps.contracts.models import Contract, RawContractData
from django.db.models import Count, Avg, Q
from decimal import Decimal

print("\n" + "="*60)
print("DATA PIPELINE EXECUTION REPORT")
print("="*60 + "\n")

# Raw Data Stats
raw_total = RawContractData.objects.count()
raw_processed = RawContractData.objects.filter(is_processed=True).count()
raw_failed = RawContractData.objects.filter(processing_error__isnull=False).exclude(processing_error="").count()

print("┌─ RAW DATA EXTRACTION")
print(f"│  Total Records: {raw_total}")
print(f"│  Processed: {raw_processed}")
print(f"│  Failed: {raw_failed}")
print("│")

# Contract Stats
contracts = Contract.objects.all()
analyzed = contracts.filter(analyzed_at__isnull=False)

print("├─ CONTRACT NORMALIZATION")
print(f"│  Total Contracts: {contracts.count()}")
print(f"│  By Source:")
for source in contracts.values('source_platform').annotate(count=Count('id')):
    print(f"│    • {source['source_platform']}: {source['count']}")
print("│")

# Risk Analysis Stats
print("├─ RISK ANALYSIS")
print(f"│  Analyzed: {analyzed.count()}/{contracts.count()}")

risk_levels = [
    (0, 20, "MINIMAL"),
    (20, 40, "LOW"),
    (40, 60, "MEDIUM"),
    (60, 75, "HIGH"),
    (75, 100, "CRITICAL")
]

for min_val, max_val, label in risk_levels:
    count = analyzed.filter(risk_score__gte=min_val, risk_score__lt=max_val).count()
    if count > 0:
        print(f"│    {label}: {count}")

avg_risk_data = analyzed.aggregate(avg=Avg('risk_score'))['avg']
avg_risk = float(avg_risk_data) if avg_risk_data else 0
print(f"│  Average Risk Score: {avg_risk:.2f}/100")
print("│")

# Type Distribution
print("├─ CONTRACT TYPE DISTRIBUTION")
for ct in contracts.values('contract_type').annotate(count=Count('id')).order_by('-count'):
    print(f"│  {ct['contract_type']}: {ct['count']}")
print("│")

# Summary
print("└─ PIPELINE STATUS")
print(f"   ✓ Pipeline execution completed successfully")
print(f"   ✓ {contracts.count()} contracts in database")
print(f"   ✓ {analyzed.count()} contracts analyzed")
print("\n" + "="*60 + "\n")
PYTHON_EOF

    print_success "Report generated"
}

# ==================== MAIN ====================

main() {
    case "${1:-all}" in
        crawl)
            crawl
            ;;
        normalize)
            normalize
            ;;
        analyze)
            analyze
            ;;
        report)
            report
            ;;
        all|pipeline)
            crawl
            normalize
            analyze
            report

            print_header "PIPELINE COMPLETE"
            print_success "All steps executed successfully!"
            ;;
        *)
            echo "Usage: $0 {crawl|normalize|analyze|report|pipeline|all}"
            echo ""
            echo "Options:"
            echo "  crawl      - Run all data crawlers"
            echo "  normalize  - Normalize raw data to contracts"
            echo "  analyze    - Run risk analysis"
            echo "  report     - Generate execution report"
            echo "  pipeline   - Run complete pipeline (default)"
            echo "  all        - Same as pipeline"
            exit 1
            ;;
    esac
}

# Execute
main "$@"
