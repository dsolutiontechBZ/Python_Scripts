import socket
import requests
import logging
import time
import os
import datetime
import subprocess
import json

def header_info():
    header = """
     _____            _       _   _          _______        _
    |  __ \          | |     | | (_)        |__   __|      | |
    | |  | |___  ___ | |_   _| |_ _  ___  _ __ | | ___  ___| |__
    | |  | / __|/ _ \| | | | | __| |/ _ \| '_ \| |/ _ \/ __| '_ \\
    | |__| \__ \ (_) | | |_| | |_| | (_) | | | | |  __/ (__| | | |
    |_____/|___/\___/|_|\__,_|\__|_|\___/|_| |_|_|\___|\___|_| |_|

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|M|o||n|i|t|o||r|_|U|p|t|i|m|e|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    print(header)

# Call the header_info function
header_info()

print("Executing script..............")

# Function to send messages via WhatsApp API
def send_message(message):
    # Add the API key and chat IDs here
    IdInstance = "7103897494"
    ApiTokenInstance = "ApiTokenInstance HERE"
    # chat ID 1
    CHAT_ID_1 = "5016151855@c.us"
    # chat ID 2
    CHAT_ID_2 = ""
    
    chat_ids = [CHAT_ID_1, CHAT_ID_2]  # Create a list of chat IDs
    
    for chat_id in chat_ids:
        url = f"https://7103.api.greenapi.com/waInstance{IdInstance}/sendMessage/{ApiTokenInstance}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "chatId": chat_id,
            "message": message
        }
        # Make the API call to send the message
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Message sent to {chat_id}")
        else:
            print(f"Failed to send message to {chat_id}")
            print(response.text)
        
# Function to get status icon based on status
def get_status_icon(status):
    return "✅" if status == "UP" else "🔴"

# logging configuration to include date, time and status
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to perform ICMP ping to a host
def ping_host(host):
    try:
        result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE)
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        return False

# Function to check URL for keyword
def check_website(url, keyword):
    try:
        response = requests.get(url)
        
        if response.status_code == 200 and keyword in response.text:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

# Function to perform TCP ping on a specific port
def tcp_ping(hostname, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((hostname, port))
        sock.close()
        return True
    except:
        return False

# Function to monitor website and log results
def monitor_website(website, previous_status):
    url = website['url']
    log_file = f"{website['name'].lower().replace(' ', '_')}_log.txt"  
    logger = logging.getLogger(f"{website['name']}_{time.strftime('%Y%m%d%H%M%S')}")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file)
    
    # logging format to include date, time and status
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    if ':' not in url:  # Check if ':' is not in the URL
        status = ping_host(website['url'])
        if status:
            logger.info(f"PING is successful, {website['name']} is up.")
            if not previous_status:
                send_message(f"[{website['name']} {get_status_icon('UP')}] is up")
        else:
            logger.info(f"PING failed, {website['name']} down")
            if previous_status:
                send_message(f"[{website['name']} {get_status_icon('DOWN')}] is down")
    else:
        if 'keyword' in website: # Check if 'keyword' is in the URL
            status = check_website(url, website['keyword'])
            if status:
                logger.info(f"Keyword found, {website['name']} is up.")
                if not previous_status:
                    send_message(f"[{website['name']} {get_status_icon('UP')}] is back online")
            else:
                logger.info(f" Keyword no found, {website['name']} is DOWN")
                if previous_status:
                    send_message(f"[{website['name']} {get_status_icon('DOWN')}]. Keyword not found")
        else:
            port = int(url.split(':')[-1])
            hostname = url.split('//')[-1].split(':')[0]
            status = tcp_ping(hostname, port)
            if status:
                logger.info(f"TCP ping is successful, {website['name']} is up.")
                if not previous_status:
                    send_message(f"[{website['name']} {get_status_icon('UP')}] is back online")
            else:
                logger.info(f"TCP ping failed, {website['name']} is down")
                if previous_status:
                    send_message(f"[{website['name']} {get_status_icon('DOWN')}]. is down")
    
    return status  # Return the current status for the next iteration

# Read URLs from a json configuration file
def read_websites_from_config():
    with open("urls_config.json", "r") as file:
        return json.load(file)

websites = read_websites_from_config()
last_modified_timestamp = os.path.getmtime("urls_config.json")  # Store the last modified timestamp

# Function to delete log files that are 90 days old
def delete_old_logs():
    log_directory = os.getcwd()  # Get current working directory
    files_to_delete = []

    for filename in os.listdir(log_directory):
        if filename.endswith("_log.txt"):
            creation_time = os.path.getctime(filename)
            if (datetime.datetime.now() - datetime.datetime.fromtimestamp(creation_time)).days >= 90:
                files_to_delete.append(filename)
                os.remove(filename)

    return files_to_delete

# Function to notify about log files to be deleted 5 days in advance
def notify_files_to_delete():
    files_to_delete = delete_old_logs()
    if files_to_delete:
        message = f"The following log files will be deleted in 5 days: {', '.join(files_to_delete)}"
        send_message(message)

# Function to send message after deleting log files
def notify_files_deleted(files_deleted):
    if files_deleted:
        message = f"The following log files have been deleted: {', '.join(files_deleted)}"
        send_message(message)

# Before running the main loop, notify about log files to be deleted
notify_files_to_delete()

# Main loop for monitoring websites
previous_statuses = {website['name']: True for website in websites}  # Initialize all websites as UP
while True:
    for website in websites:
        previous_status = previous_statuses[website['name']]
        current_status = monitor_website(website, previous_status)
        previous_statuses[website['name']] = current_status
    time.sleep(30)  # Check every 30 seconds
    
# Check if the configuration file has been modified
    current_timestamp = os.path.getmtime("urls_config.json")
    if current_timestamp != last_modified_timestamp:
        last_modified_timestamp = current_timestamp
        websites = read_websites_from_config()
        
# After the main loop, notify about the log files that have been deleted
files_deleted = delete_old_logs()
notify_files_deleted(files_deleted)
