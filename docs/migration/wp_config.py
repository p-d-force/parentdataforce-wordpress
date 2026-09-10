# WordPress Configuration for Parent Data Force Migration

# NOTE: legacy/superseded. Current tooling reads rest/credentials.json instead.
# The live REST URL is https://www.parentdataforce.com/news/wp-json/ (not localhost).
WP_API_URL = "http://localhost/wp-json/wp/v2"

# Authentication (Application Password)
# The WP login is "pdforce" (user id 1); "admin" is only its display name and is NOT
# a registered login. Verified against wp-login.php. credentials.json already uses pdforce.
WP_USERNAME = "pdforce"
WP_APPLICATION_PASSWORD = "YOUR_APP_PASSWORD_HERE"

# Site Information
SITE_TITLE = "Parent Data Force"
SITE_DESCRIPTION = "Data-driven advocacy for families. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts."
SITE_TAGLINE = "MAKING DATA MAKE SENSE"

# Branding Colors
PRIMARY_BG = "#0b0b0b"
SECONDARY_BG = "#161616"
ACCENT_COLOR = "#ff5a1f"
ACCENT_GLOW = "#ffa366"
TEXT_PRIMARY = "#f5f5f5"
TEXT_SECONDARY = "#a0a0a0"
TEXT_MUTED = "#767676"

# Custom Post Types
CUSTOM_POST_TYPES = [
    "cases",
    "districts",
    "resources",
    "appearances"
]