"""Analytics models."""
from django.db import models

# Analytics will primarily use services and don't need many models
# Most analytics will be computed on-the-fly or cached

# This file exists to satisfy Django's app structure
# but can be extended with models like:
# - CachedAnalytics (for expensive computations)
# - Report (for generated reports)
# - Alert (system-wide alerts, different from provider alerts)
