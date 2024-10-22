import configparser
import os
from prettytable import PrettyTable
import sys

# ANSI escape codes for colors
RED = "\033[91m"  # Red for error messages
YELLOW = "\033[93m"  # Yellow for warning messages
RESET = "\033[0m"  # Reset color

# Load the config.ini file
config_file = "config/python_app/media.ini"
config = configparser.ConfigParser()

if os.path.exists(config_file):
    config.read(config_file)
else:
    print(f"Configuration File {config_file} not found.")
    sys.exit(1)

def save_config():
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print("Changes saved.")

def sanitize_input(text):
    return text.replace('"', '').replace("'", "").strip()

def display_error(message):
    print(f"{RED}Error: {message}{RESET}")

def display_warning(message):
    print(f"{YELLOW}Warning: {message}{RESET}")

def validate_url(media_type, url):
    if media_type == 'rtsp':
        if not url.startswith('rtsp://'):
            return False, "RTSP URL must start with 'rtsp://'."
    elif media_type == 'file':
        if not os.path.isfile(url):
            return False, f"The file '{url}' does not exist."
    elif media_type == 'youtube':
        if not url.startswith('https://'):
            return False, "YouTube URL must start with 'https://'."
    elif media_type in ['http', 'https']:
        if not (url.startswith('http://') or url.startswith('https://')):
            return False, "HTTP/HTTPS URL must start with 'http://' or 'https://'."
    
    return True, ""

def add_media():
    media_types = {
        '1': 'youtube',
        '2': 'rtsp',
        '3': 'file',
        '4': 'http',
        '5': 'https'
    }

    print("Choose media type:")
    for key, value in media_types.items():
        print(f"{key}. {value}")

    media_type_choice = input("Enter the number of the media type: ").strip()
    media_type = media_types.get(media_type_choice)

    if not media_type:
        display_error("Invalid media type selected.")
        return

    media_name = sanitize_input(input("Enter media name: ").strip())
    url = input("Enter the URL: ").strip()
    
    # Validate the URL based on the selected media type
    is_valid, message = validate_url(media_type, url)
    if not is_valid:
        display_error(message)
        return

    enable = input("Enable this media? (yes/no): ").strip().lower()
    enable_value = '1' if enable in ['yes', 'y'] else '0'
    
    # Find the next available index without exposing the Media ID
    index = 0
    while f'MediaSettings-{index}' in config:
        index += 1
    
    section = f'MediaSettings-{index}'
    config[section] = {
        'media_name': media_name,
        'type': media_type,
        'url': url,
        'enable': enable_value
    }
    print(f"Added {media_name} with type {media_type} and URL {url}.")
    save_config()

def remove_media():
    print("\nAvailable Media Sources:")
    table = PrettyTable()
    table.field_names = ["Index", "Media Name", "Media Type", "URL"]
    
    # Set alignment: center index, left-align other columns
    table.align["Index"] = "c"  # Center align index
    table.align["Media Name"] = "l"  # Left align media name
    table.align["Media Type"] = "l"  # Left align media type
    table.align["URL"] = "l"  # Left align URL
    
    media_list = []  # Store media sections for accurate indexing

    for count, section in enumerate(config.sections(), start=1):
        media_name = sanitize_input(config[section]['media_name'])
        media_type = config[section]['type']
        url = config[section]['url']
        table.add_row([count, media_name, media_type, url])
        media_list.append(section)  # Keep track of the sections
    
    print(table)
    
    choice = input("Enter the user-friendly index to remove (or 'c' to cancel): ").strip()
    if choice.lower() == 'c':
        print("Removal cancelled.")
        return
    
    try:
        index = int(choice) - 1  # Convert to zero-based index
        if 0 <= index < len(media_list):
            section = media_list[index]  # Use the tracked section for removal
            media_name = config[section]['media_name']
            config.remove_section(section)
            print(f"{media_name} removed.")
            save_config()
        else:
            display_error(f"Media with index {index + 1} not found.")
    except (ValueError, IndexError):
        display_error("Invalid index format. Please enter a valid number.")

def list_summary():
    active_count = sum(1 for section in config.sections() if config[section]['enable'] == '1')
    inactive_count = sum(1 for section in config.sections() if config[section]['enable'] == '0')

    summary_table = PrettyTable()
    summary_table.field_names = ["Status", "Count"]
    summary_table.add_row(["Active", active_count])
    summary_table.add_row(["Inactive", inactive_count])
    print("Media Summary:")
    print(summary_table)

def list_media():
    print("\nAll Media Sources:")
    table = PrettyTable()
    table.field_names = [ "Media Name", "Media Type", "URL", "Status"]
    
    # Set alignment: center index, left-align other columns
    #table.align["Index"] = "c"  # Center align index
    table.align["Media Name"] = "l"  # Left align media name
    table.align["Media Type"] = "l"  # Left align media type
    table.align["URL"] = "l"  # Left align URL
    table.align["Status"] = "l"  # Left align status
    
    for count, section in enumerate(config.sections(), start=1):
        media_name = sanitize_input(config[section]['media_name'])
        media_type = config[section]['type']
        url = config[section]['url']
        status = "Enabled" if config[section]['enable'] == '1' else "Disabled"
        table.add_row([media_name, media_type, url, status])
    
    print(table)

def activate_media():
    print("\nInactive Media Sources:")
    inactive_medias = [(section, config[section]['media_name']) for section in config.sections() if config[section]['enable'] == '0']
    
    if not inactive_medias:
        display_error("No inactive media sources available.")
        return

    table = PrettyTable()
    table.field_names = ["Index", "Media Name", "Media Type", "URL"]
    
    # Set alignment: center index, left-align other columns
    table.align["Index"] = "c"  # Center align index
    table.align["Media Name"] = "l"  # Left align media name
    table.align["Media Type"] = "l"  # Left align media type
    table.align["URL"] = "l"  # Left align URL
    
    for i, (section, media_name) in enumerate(inactive_medias, 1):
        table.add_row([i, sanitize_input(media_name), config[section]['type'], config[section]['url']])
    
    print(table)
    
    choice = input("Enter the number of the media to activate (or 'c' to cancel): ").strip()
    if choice.lower() == 'c':
        print("Activation cancelled.")
        return
    
    try:
        index = int(choice) - 1
        section, media_name = inactive_medias[index]
        config[section]['enable'] = '1'
        print(f"{media_name} has been activated.")
        save_config()
    except (IndexError, ValueError):
        display_error("Invalid choice. Please try again.")

def deactivate_media():
    print("\nActive Media Sources:")
    active_medias = [(section, config[section]['media_name']) for section in config.sections() if config[section]['enable'] == '1']
    
    if not active_medias:
        display_error("No active media sources available.")
        return

    table = PrettyTable()
    table.field_names = ["Index", "Media Name", "Media Type", "URL"]
    
    # Set alignment: center index, left-align other columns
    table.align["Index"] = "c"  # Center align index
    table.align["Media Name"] = "l"  # Left align media name
    table.align["Media Type"] = "l"  # Left align media type
    table.align["URL"] = "l"  # Left align URL
    
    for i, (section, media_name) in enumerate(active_medias, 1):
        table.add_row([i, sanitize_input(media_name), config[section]['type'], config[section]['url']])
    
    print(table)
    
    choice = input("Enter the number of the media to deactivate (or 'c' to cancel): ").strip()
    if choice.lower() == 'c':
        print("Deactivation cancelled.")
        return
    
    try:
        index = int(choice) - 1
        section, media_name = active_medias[index]
        config[section]['enable'] = '0'
        print(f"{media_name} has been deactivated.")
        save_config()
    except (IndexError, ValueError):
        display_error("Invalid choice. Please try again.")

def show_menu():
    list_summary()
    print("\nMenu:")
    menu = PrettyTable()
    menu.field_names = ["Index", "Option"]
    
    # Set alignment: center index, left-align option
    menu.align["Index"] = "c"  # Center align index
    menu.align["Option"] = "l"  # Left align option
    
    menu.add_row(["1", "Add Media"])
    menu.add_row(["2", "Remove Media"])
    menu.add_row(["3", "List Media"])
    menu.add_row(["4", "Deactivate Media"])
    menu.add_row(["5", "Activate Media"])
    menu.add_row(["0", "Finish"])
    
    print(menu)

def manage_source():
    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == '1':
            add_media()
        elif choice == '2':
            remove_media()
        elif choice == '3':
            list_media()
        elif choice == '4':
            deactivate_media()
        elif choice == '5':
            activate_media()
        elif choice == '0':
            print("Exiting...")
            break
        else:
            display_error("Invalid option selected.")
    num_active_sources = sum(1 for section in config.sections() if config[section]['enable'] == '1')
    return num_active_sources
