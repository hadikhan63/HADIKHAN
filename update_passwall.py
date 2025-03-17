#!/usr/bin/env python3

import time
import requests
import os
import logging
import shutil
import re

# Configure logging
LOG_FILE = "/var/log/passwall_update.log"
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Path to the passwall2 config file
PASSWALL_FILE = "/etc/config/passwall2"
TEMP_FILE = "/tmp/passwall2_temp"

# GitHub URLs containing the new lists
DOMAIN_LIST_URL = "https://raw.githubusercontent.com/hadikhan63/HADIKHAN/main/List"
BLOCK_LIST_URL = "https://raw.githubusercontent.com/hadikhan63/HADIKHAN/main/Block"

# Wait for 30 seconds after boot
time.sleep(30)

def fetch_list(url, list_name):
    """Fetch a list from GitHub."""
    logging.debug(f"Fetching {list_name} from {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        items = response.text.strip().split("\n")
        logging.info(f"Fetched {len(items)} items for {list_name}.")
        return items
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {list_name}: {e}")
        return None

def update_passwall_file(domain_list, block_list):
    """Modify the domain_list and Block sections inside the passwall2 config file."""
    logging.debug("Starting to update the passwall2 file...")
    if not os.path.exists(PASSWALL_FILE):
        logging.error(f"Error: {PASSWALL_FILE} not found.")
        return False

    with open(PASSWALL_FILE, "r", encoding="utf-8") as file:
        content = file.read()
        logging.debug("Original passwall2 file content read successfully.")

    # Update the domain_list section
    domain_pattern = re.compile(r"(option domain_list ')(.*?)(')", re.DOTALL)
    match_domain = domain_pattern.search(content)

    if match_domain:
        new_domain_list = "\n".join(domain_list) + "\n"
        content = content[:match_domain.start(2)] + new_domain_list + content[match_domain.end(2):]
        logging.debug("Updated domain_list section successfully.")
    else:
        logging.error("Error: Unable to locate the domain_list section.")

    # Update the Block section (config shunt_rules 'Block')
    block_pattern = re.compile(r"(config shunt_rules 'Block'\s+.*?option rules ')(.*?)(')", re.DOTALL)
    match_block = block_pattern.search(content)

    if match_block:
        new_block_list = "\n".join(block_list) + "\n"
        content = content[:match_block.start(2)] + new_block_list + content[match_block.end(2):]
        logging.debug("Updated Block section successfully.")
    else:
        logging.error("Error: Unable to locate the Block section.")

    # Ensure the option enabled is set to 1
    content = re.sub(r"option enabled '\d'", "option enabled '1'", content)

    # Write changes to a temporary file
    with open(TEMP_FILE, "w", encoding="utf-8") as file:
        file.write(content)
        logging.debug("Updated content written to temporary file successfully.")

    # Replace the original file with the modified one
    shutil.move(TEMP_FILE, PASSWALL_FILE)
    logging.info("Updated passwall2 file successfully.")
    return True

def restart_passwall():
    """Restart the passwall service to apply changes."""
    logging.debug("Attempting to restart the passwall service...")
    result = os.system("/etc/init.d/passwall2 restart")
    if result == 0:
        logging.info("Passwall service restarted successfully.")
    else:
        logging.error("Failed to restart Passwall service.")

# Execute the update process
logging.info("Passwall update script started.")

domain_list = fetch_list(DOMAIN_LIST_URL, "domain_list")
block_list = fetch_list(BLOCK_LIST_URL, "Block")

if domain_list and block_list:
    if update_passwall_file(domain_list, block_list):
        restart_passwall()

logging.info("Passwall update script completed.")
