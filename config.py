import os

# CONFIGURATION 
# Uses os.getenv() to pull from Azure Settings / local.settings.json

ADX_CLUSTER           = os.getenv("ADX_CLUSTER")
ADX_DB                = os.getenv("ADX_DB")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY      = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_MODEL    = os.getenv("AZURE_OPENAI_MODEL", "gpt-4-ops") # Default provided
AZURE_API_VERSION     = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
SENDER_ADDRESS        = os.getenv("SENDER_ADDRESS")
RECIPIENT_EMAIL       = os.getenv("RECIPIENT_EMAIL")
FILTER_COUNTRY        = os.getenv("FILTER_COUNTRY", "UK")

# Reporting Period

CURRENT_WEEK_START    = "2025-11-24" 
CURRENT_WEEK_END      = "2025-11-30"

