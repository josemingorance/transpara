"""Region extraction utilities for Spanish autonomous communities.

Extracts region information from contracting authority names based on
keyword matching against Spanish autonomous communities and provinces.
"""
from typing import Optional, Dict, List
import logging


class RegionExtractor:
    """Extracts Spanish autonomous community from authority name.
    
    Maps authority names containing city or province names to their
    corresponding autonomous community (Comunidad Autónoma).
    """
    
    # Mapping of autonomous communities to their keywords (cities, provinces, etc.)
    REGION_KEYWORDS: Dict[str, List[str]] = {
        "Andalucía": [
            "andalucía", "andalusia", "sevilla", "córdoba", "málaga",
            "cádiz", "huelva", "jaén", "almería", "granada"
        ],
        "Aragón": [
            "aragón", "aragon", "zaragoza", "huesca", "teruel"
        ],
        "Asturias": [
            "asturias", "oviedo"
        ],
        "Illes Balears": [
            "balears", "baleares", "balear", "palma", "mallorca",
            "menorca", "ibiza", "formentera"
        ],
        "País Vasco": [
            "país vasco", "vasco", "euskadi", "basque", "bilbao",
            "vizcaya", "bizkaia", "guipúzcoa", "gipuzkoa", "álava", "araba"
        ],
        "Canarias": [
            "canarias", "canary", "gran canaria", "tenerife",
            "lanzarote", "fuerteventura", "la palma", "la gomera", "el hierro"
        ],
        "Cantabria": [
            "cantabria", "santander"
        ],
        "Castilla-La Mancha": [
            "castilla-la mancha", "castilla la mancha", "cuenca",
            "guadalajara", "toledo", "ciudad real", "albacete"
        ],
        "Castilla y León": [
            "castilla y león", "castilla león", "valladolid", "burgos",
            "león", "salamanca", "segovia", "soria", "palencia",
            "zamora", "ávila"
        ],
        "Cataluña": [
            "cataluña", "catalunya", "catalonia", "barcelona",
            "girona", "lleida", "tarragona"
        ],
        "Comunidad de Madrid": [
            "madrid", "comunidad de madrid"
        ],
        "Comunidad Foral de Navarra": [
            "navarra", "navarre", "nafarroa", "pamplona", "iruña"
        ],
        "Extremadura": [
            "extremadura", "badajoz", "cáceres"
        ],
        "Galicia": [
            "galicia", "galician", "a coruña", "coruña", "lugo",
            "ourense", "orense", "pontevedra", "santiago"
        ],
        "La Rioja": [
            "rioja", "logroño"
        ],
        "Región de Murcia": [
            "murcia", "región de murcia"
        ],
        "Comunitat Valenciana": [
            "valencia", "valenciana", "valència", "alicante",
            "alacant", "castellón", "castelló"
        ],
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize region extractor.
        
        Args:
            logger: Optional logger for debugging
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_region(self, authority: str) -> str:
        """Extract autonomous community from authority name.
        
        Uses keyword matching to identify the region based on city,
        province, or region names in the authority string.
        
        Args:
            authority: Contracting authority name
            
        Returns:
            Autonomous community name or empty string if not found
            
        Examples:
            >>> extractor = RegionExtractor()
            >>> extractor.extract_region("Ayuntamiento de Barcelona")
            'Cataluña'
            >>> extractor.extract_region("Junta de Andalucía")
            'Andalucía'
        """
        if not authority:
            return ""
        
        authority_lower = authority.lower()
        
        # Check each region's keywords
        for region, keywords in self.REGION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in authority_lower:
                    self.logger.debug(
                        f"Matched region '{region}' for authority '{authority}' "
                        f"using keyword '{keyword}'"
                    )
                    return region
        
        self.logger.debug(f"No region found for authority: {authority}")
        return ""
    
    def get_all_regions(self) -> List[str]:
        """Get list of all supported autonomous communities.
        
        Returns:
            List of region names
        """
        return list(self.REGION_KEYWORDS.keys())
    
    def validate_region(self, region: str) -> bool:
        """Check if region name is valid.
        
        Args:
            region: Region name to validate
            
        Returns:
            True if region is in the supported list
        """
        return region in self.REGION_KEYWORDS
