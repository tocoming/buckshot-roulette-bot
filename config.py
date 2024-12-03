import os
from dotenv import load_dotenv

from i18n import I18n  
from logger import logger  

load_dotenv('.env')
API_TOKEN = os.getenv('TOKEN')

if not API_TOKEN:
    logger.error("❌ API token not found. Please add it to the .env file.")
    raise ValueError("❌ API token not found. Please add it to the .env file.")

i18n = I18n(locale_path="locales/translations.json", default_lang="eng")
