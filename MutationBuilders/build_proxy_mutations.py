import os
import logging
from tqdm import tqdm
import sys
import warnings
import traceback

from MutationBuilders.static_proxy_mutation_builder import StaticProxyMutationBuilder
from MutationBuilders.static_mutation_config_builder import StaticMutationConfigBuilder

# --- Unique Logger Setup ---
def get_unique_logger():
    logger = logging.getLogger("mutation_engine")
    if not getattr(logger, "_is_configured", False):
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.propagate = False  # Prevent messages from being passed to the root logger
        logger._is_configured = True
    return logger

logging = get_unique_logger()

if __name__ == "__main__":
    api_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'APIs'))
    print("api_dir", api_dir)
    sys.path.insert(0, api_dir)
    services = [d for d in os.listdir(api_dir) if os.path.isdir(os.path.join(api_dir, d))]
    services = [s for s in services if s not in ('common_utils', '__pycache__')]

    # for service in tqdm(['notes_and_lists', 'google_maps', 'google_home', 'google_calendar', 'device_setting', 'generic_media', 'messages', 'google_sheets', 'google_chat', 'google_cloud_storage', 'puppeteer', 'copilot', 'cursor', 'workday', 'azure', 'media_control', 'google_meet', 'contacts', 'spotify', 'canva', 'shopify', 'terminal', 'retail', 'bigquery', 'google_docs', 'gdrive', 'youtube', 'google_slides', 'Schemas', 'mongodb', 'sapconcur', 'device_actions', 'supabase', 'hubspot', 'google_search', 'gemini_cli', 'home_assistant', 'jira', 'github', 'figma', 'github_actions', 'zendesk', 'google_people', 'mysql'], desc="Building proxy mutations", unit="service"):
    # for service in tqdm(['puppeteer'], desc="Building proxy mutations", unit="service"):
    for service in tqdm(services, desc="Building proxy mutations", unit="service"):
        logging.info(f"\n--- Building proxy mutation for service: {service} ---")
        try:
            StaticMutationConfigBuilder(service_name=service, mutation_name="m01", regenerate=False, sync_latest=True).build()
            StaticProxyMutationBuilder(service_name=service, config_name="m01", regenerate=True, include_original_functions=False).build()
            logging.info(f"--- Successfully built proxy mutation for {service} ---\n")
        except FileNotFoundError as e:
            logging.error(f"Error building proxy mutation for {service}: {e}\n")
            traceback.print_exc()
        except Exception as e:
            logging.error(f"An unexpected error occurred for {service}: {e}\n")
            traceback.print_exc()
