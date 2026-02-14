# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 17:37:09 2026

@author: User
"""

# utils/config.py
import os
import logging
from dotenv import load_dotenv

# Initialize Logger
logger = logging.getLogger("Config")

# Load .env file immediately. 
# find_dotenv() searches for .env in the project root automatically.
# If you run this in an environment without a .env file (like Docker), it will just skip it.
if not load_dotenv():
    logger.warning("No .env file found. Ensure environment variables are set.")

def get_sonoff_creds():
    return {
        'app_id': os.getenv('SONOFF_APP_ID'),           # Maps to APP_ID in .env
        'app_secret': os.getenv('SONOFF_APP_SECRET'),   # Maps to APP_SECRET in .env
        'access_token': os.getenv('SONOFF_ACCESS_TOKEN'),
        'region': os.getenv('SONOFF_REGION', 'as') # Default to 'as' if missing
    }

def get_tuya_creds():
    return {
        'api_key': os.getenv('TUYA_API_KEY'),
        'api_secret': os.getenv('TUYA_API_SECRET'),
        'device_id': os.getenv('TUYA_DEVICE_ID'),
        'region': os.getenv('TUYA_REGION', 'eu') # Default to 'eu' if missing
    }

def get_sensibo_creds():
    return {
        'api_key': os.getenv('SENSIBO_API_KEY')
    }