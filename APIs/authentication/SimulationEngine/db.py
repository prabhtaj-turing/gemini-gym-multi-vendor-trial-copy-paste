"""
Authentication Service Database

Manages authentication-related data and service metadata.
"""

# Authentication service database
DB = {
    "services": {
        "airline": {"name": "airline", "description": "Airline booking and management"},
        "azure": {"name": "azure", "description": "Microsoft Azure cloud services"},
        "bigquery": {"name": "bigquery", "description": "Google BigQuery data warehouse"},
        "blender": {"name": "blender", "description": "3D modeling and animation software"},
        "canva": {"name": "canva", "description": "Graphic design platform"},
        "clock": {"name": "clock", "description": "Time and alarm management"},
        "confluence": {"name": "confluence", "description": "Team collaboration and documentation"},
        "contacts": {"name": "contacts", "description": "Contact management system"},
        "copilot": {"name": "copilot", "description": "AI-powered code assistance"},
        "cursor": {"name": "cursor", "description": "AI-powered code editor"},
        "device_actions": {"name": "device_actions", "description": "Device control and automation"},
        "device_setting": {"name": "device_setting", "description": "Device configuration management"},
        "figma": {"name": "figma", "description": "Collaborative design tool"},
        "gdrive": {"name": "gdrive", "description": "Google Drive cloud storage"},
        "gemini_cli": {"name": "gemini_cli", "description": "Gemini AI command line interface"},
        "generic_media": {"name": "generic_media", "description": "Media playback and control"},
        "generic_reminders": {"name": "generic_reminders", "description": "Reminder and notification system"},
        "generic_tools": {"name": "generic_tools", "description": "General utility tools"},
        "github": {"name": "github", "description": "Git repository hosting service"},
        "github_actions": {"name": "github_actions", "description": "GitHub CI/CD workflows"},
        "gmail": {"name": "gmail", "description": "Google email service"},
        "google_calendar": {"name": "google_calendar", "description": "Google Calendar scheduling"},
        "google_chat": {"name": "google_chat", "description": "Google Chat messaging"},
        "google_cloud_storage": {"name": "google_cloud_storage", "description": "Google Cloud Storage"},
        "google_docs": {"name": "google_docs", "description": "Google Docs document editing"},
        "google_home": {"name": "google_home", "description": "Google Home smart devices"},
        "google_maps": {"name": "google_maps", "description": "Google Maps navigation"},
        "google_meet": {"name": "google_meet", "description": "Google Meet video conferencing"},
        "google_people": {"name": "google_people", "description": "Google People contact management"},
        "google_search": {"name": "google_search", "description": "Google Search engine"},
        "google_sheets": {"name": "google_sheets", "description": "Google Sheets spreadsheet"},
        "google_slides": {"name": "google_slides", "description": "Google Slides presentations"},
        "home_assistant": {"name": "home_assistant", "description": "Home automation platform"},
        "hubspot": {"name": "hubspot", "description": "CRM and marketing platform"},
        "instagram": {"name": "instagram", "description": "Social media platform"},
        "jira": {"name": "jira", "description": "Project management and issue tracking"},
        "linkedin": {"name": "linkedin", "description": "Professional networking platform"},
        "media_control": {"name": "media_control", "description": "Media device control"},
        "messages": {"name": "messages", "description": "Messaging applications"},
        "mongodb": {"name": "mongodb", "description": "NoSQL database"},
        "mysql": {"name": "mysql", "description": "Relational database management"},
        "notes_and_lists": {"name": "notes_and_lists", "description": "Note-taking and list management"},
        "notifications": {"name": "notifications", "description": "System notifications"},
        "phone": {"name": "phone", "description": "Phone call management"},
        "puppeteer": {"name": "puppeteer", "description": "Web automation and scraping"},
        "reddit": {"name": "reddit", "description": "Social news aggregation platform"},
        "retail": {"name": "retail", "description": "E-commerce and retail operations"},
        "salesforce": {"name": "salesforce", "description": "Customer relationship management"},
        "sapconcur": {"name": "sapconcur", "description": "Expense and travel management"},
        "sdm": {"name": "sdm", "description": "Smart device management"},
        "shopify": {"name": "shopify", "description": "E-commerce platform"},
        "slack": {"name": "slack", "description": "Team communication platform"},
        "spotify": {"name": "spotify", "description": "Music streaming service"},
        "stripe": {"name": "stripe", "description": "Payment processing platform"},
        "supabase": {"name": "supabase", "description": "Backend-as-a-service platform"},
        "terminal": {"name": "terminal", "description": "Command line interface"},
        "tiktok": {"name": "tiktok", "description": "Short-form video platform"},
        "whatsapp": {"name": "whatsapp", "description": "Messaging application"},
        "workday": {"name": "workday", "description": "Human capital management"},
        "youtube": {"name": "youtube", "description": "Video sharing platform"},
        "zendesk": {"name": "zendesk", "description": "Customer service platform"}
    },
    "authentication_sessions": {},
    "authentication_logs": []
}

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
