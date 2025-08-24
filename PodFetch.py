#!/usr/bin/python3
# Podfetch
# G0JPS August 2025

import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import re
import glob
import time

# --- ANSI Color Codes for readability in the terminal ---
class Colors:
	GREEN = '\033[92m'
	BLUE = '\033[94m'
	YELLOW = '\033[93m'
	CYAN = '\033[96m'
	RED = '\033[1;31m'
	BOLD = '\033[1m'
	RESET = '\033[0m'

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPML_FILE_PATH = None

# ASCII art for title
ASCII_ART = r"""
-----------------------------------------
 ____           _ _____    _       _
|  _ \ ___   __| |  ___|__| |_ ___| |__
| |_) / _ \ / _` | |_ / _ \ __/ __| '_ \
|  __/ (_) | (_| |  _|  __/| | (__| | | |
|_|   \___/ \__,_|_|  \___|\__\___|_| |_|

The Easy Podcast Fetcher      G0JPS 08/25
-----------------------------------------
"""

# Clear the screen to keep UI tidy
def clear_screen():
	# For Windows
	if os.name == 'nt':
		_ = os.system('cls')
	# For macOS and Linux
	else:
		_ = os.system('clear')

def get_opml_files(directory):
	# Find all files ending with .opml in a given directory and return a list of their full paths.
	return glob.glob(os.path.join(directory, '*.opml'))

def get_podcasts_from_opml(file_path):
	# Parse an OPML file and returns a list of podcast titles and URLs.
	podcasts = []
	try:
		tree = ET.parse(file_path)
		root = tree.getroot()
		for outline in root.findall('.//outline'):
			title = outline.get('title')
			url = outline.get('xmlUrl')
			if title and url:
				podcasts.append({'title': title, 'url': url})
	except FileNotFoundError:
		print(f"{Colors.YELLOW}Error:{Colors.RESET} The file '{os.path.basename(file_path)}' was not found.")
		time.sleep(2)
		sys.exit(1)
	return podcasts

def get_episodes_from_rss(feed_url):
	# Fetch and parse an RSS feed to get a list of episode titles and URLs.
	episodes = []
	try:
		# Provide a user agent to handle feeds that might block requests
		req = urllib.request.Request(feed_url, headers={'User-Agent': 'Podfetch-v10.5'})
		with urllib.request.urlopen(req) as response:
			rss_content = response.read()
			root = ET.fromstring(rss_content)
			
			# CRITICAL FIX: Use root.iter('item') to find all 'item' elements anywhere in the tree.
			# Then, check for the existence of child elements before accessing their attributes.
			for item in root.iter('item'):
				title_elem = item.find('title')
				enclosure_elem = item.find('enclosure')
				if title_elem is not None and enclosure_elem is not None:
					title = title_elem.text
					url = enclosure_elem.get('url')
					if title and url:
						episodes.append({'title': title, 'url': url})
	except Exception as e:
		print(f"{Colors.YELLOW}Error fetching or parsing RSS feed:{Colors.RESET} {e}")
	return episodes

def add_podcast_to_opml(opml_path):
	# Ask the user for a new podcast RSS URL and title, then add it to the OPML file.
	clear_screen()
	print(f"{Colors.GREEN}-------------------------------------{Colors.RESET}")
	print(f"{Colors.BOLD} Add a new podcast to the OPML file:{Colors.RESET}")
	print(f"{Colors.GREEN}-------------------------------------{Colors.RESET}")
	print(f"{Colors.YELLOW} RSS feed URLs can be found using{Colors.RESET}")
	print(f"{Colors.YELLOW} the search at {Colors.BOLD}podcastindex.org{Colors.RESET}")
	print(f"{Colors.GREEN}-------------------------------------\n{Colors.RESET}")
	podcast_title = input("Enter podcast title: ")
	podcast_url = input("Enter podcast RSS URL: ")

	if not podcast_title or not podcast_url:
		print(f"{Colors.YELLOW}Title or URL cannot be empty. No podcast added.{Colors.RESET}")
		time.sleep(2)
		return

	try:
		tree = ET.parse(opml_path)
		root = tree.getroot()
		body = root.find('body')
		if body is None:
			# Create a body if it doesn't exist
			body = ET.SubElement(root, 'body')

		new_outline = ET.SubElement(body, 'outline', type='rss', title=podcast_title, xmlUrl=podcast_url)
		tree.write(opml_path, encoding='utf-8', xml_declaration=True)
		print(f"{Colors.GREEN}Successfully added '{podcast_title}' to the OPML file!{Colors.RESET}")
	except Exception as e:
		print(f"{Colors.YELLOW}Error adding podcast:{Colors.RESET} {e}")
	
	time.sleep(2)

def remove_podcast_from_opml(opml_path):
	# Allows the user to select and remove a podcast entry from the OPML file.
	clear_screen()
	print(f"{Colors.GREEN}-------------------------------------{Colors.RESET}")
	print(f"{Colors.BOLD} Remove a podcast from the OPML file:{Colors.RESET}")
	print(f"{Colors.GREEN}-------------------------------------\n{Colors.RESET}")
	
	podcasts = get_podcasts_from_opml(opml_path)
	if not podcasts:
		print(f"No podcasts found in the OPML file '{os.path.basename(opml_path)}'.")
		time.sleep(2)
		return

	# Display the podcasts with their index for selection
	for i, p in enumerate(podcasts):
		print(f"{Colors.BLUE}{i + 1}.{Colors.RESET} {p['title']}")
	
	print(f"{Colors.YELLOW}q.{Colors.RESET} Back to Main Menu")

	try:
		choice_str = input(f"\n{Colors.BOLD}Enter the number of the podcast to remove:{Colors.RESET} ")
		if choice_str.lower() == 'q':
			print(f"\n{Colors.GREEN}Returning to main menu...{Colors.RESET}")
			time.sleep(1)
			return

		choice_index = int(choice_str) - 1
		if not (0 <= choice_index < len(podcasts)):
			print(f"{Colors.YELLOW}Invalid choice. Please enter a number from the list.{Colors.RESET}")
			time.sleep(2)
			return
			
		podcast_to_remove = podcasts[choice_index]
		confirm = input(f"Are you sure you want to remove '{podcast_to_remove['title']}'? ({Colors.BOLD}y{Colors.RESET}/{Colors.BOLD}n{Colors.RESET})".format(Colors=Colors)).lower()
		
		if confirm in ['y', 'yes']:
			tree = ET.parse(opml_path)
			root = tree.getroot()
			body = root.find('body')
			
			# Find the outline element by title and remove it
			for outline in body.findall('outline'):
				if outline.get('title') == podcast_to_remove['title']:
					body.remove(outline)
					tree.write(opml_path, encoding='utf-8', xml_declaration=True)
					print(f"{Colors.GREEN}Successfully removed '{podcast_to_remove['title']}'.{Colors.RESET}")
					break
			else:
				print(f"{Colors.YELLOW}Error: Podcast not found in file.{Colors.RESET}")
		else:
			print(f"{Colors.YELLOW}Operation cancelled.{Colors.RESET}")
			
	except ValueError:
		print(f"{Colors.YELLOW}Invalid input. Please enter a number or 'q'.{Colors.RESET}")
	except Exception as e:
		print(f"{Colors.YELLOW}Error removing podcast:{Colors.RESET} {e}")

	time.sleep(2)


def create_new_opml_file():
	# Ask the user for a filename and create a new, blank OPML file.
	clear_screen()
	print(f"{Colors.GREEN}-------------------------{Colors.RESET}")
	print(f"{Colors.BOLD} Create a new OPML file:{Colors.RESET}")
	print(f"{Colors.GREEN}-------------------------\n{Colors.RESET}")
	
	filename = input("Enter the new OPML filename (e.g., 'my_podcasts.opml'): ")
	
	if not filename.lower().endswith('.opml'):
		filename += '.opml'

	file_path = os.path.join(SCRIPT_DIR, filename)
	
	if os.path.exists(file_path):
		print(f"{Colors.YELLOW}Warning:{Colors.RESET} A file named '{filename}' already exists.")
		overwrite = input("Do you want to overwrite it? ({Colors.BOLD}y{Colors.RESET}/{Colors.BOLD}n{Colors.RESET})".format(Colors=Colors)).lower()
		if overwrite not in ['y', 'yes']:
			print(f"{Colors.YELLOW}Operation cancelled.{Colors.RESET}")
			time.sleep(2)
			return
			
	try:
		opml_template = ET.Element('opml', version='1.0')
		head_elem = ET.SubElement(opml_template, 'head')
		ET.SubElement(head_elem, 'title').text = filename.replace('.opml', '')
		ET.SubElement(opml_template, 'body')

		tree = ET.ElementTree(opml_template)
		tree.write(file_path, encoding='utf-8', xml_declaration=True)
		print(f"{Colors.GREEN}Successfully created new OPML file: '{filename}'!{Colors.RESET}")
	except Exception as e:
		print(f"{Colors.YELLOW}Error creating file:{Colors.RESET} {e}")
	
	time.sleep(2)
	return file_path

def download_file(url, file_path, referer_url):
	# Download a file from a URL to a specified path with a custom Referer header.
	try:
		print(f"  {Colors.CYAN}Downloading:{Colors.RESET} {os.path.basename(file_path)}")
		
		# Create a request object with a Referer header to handle private feeds
		req = urllib.request.Request(url, headers={'Referer': referer_url, 'User-Agent': 'Podfetch-v10.2'})
		
		with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
			data = response.read()
			out_file.write(data)
	except Exception as e:
		print(f"{Colors.YELLOW}Error downloading file:{Colors.RESET} {e}")

def sanitize_filename(filename):
	# Sanitizes a string to be a valid filename, allowing for Unicode characters.
	return re.sub(r'[^\w\s.-]', '', filename).strip()

def download_podcast_menu(opml_path):
	# Present the podcast and episode selection menus for downloading.
	while True: # Main loop for podcast selection
		clear_screen()
		# Get list of podcasts
		podcasts = get_podcasts_from_opml(opml_path)
		if not podcasts:
			print(f"No podcasts found in the OPML file '{os.path.basename(opml_path)}'.")
			time.sleep(2)
			break # Exit to the main menu

		# Present a menu of podcasts
		print(f"{Colors.GREEN}------------------------------------{Colors.RESET}")
		print(f"{Colors.BOLD} Select a podcast to download from:{Colors.RESET}")
		print(f"{Colors.GREEN}------------------------------------\n{Colors.RESET}")
		for i, p in enumerate(podcasts):
			print(f"{Colors.BLUE}{i + 1}.{Colors.RESET} {p['title']}")
		print(f"{Colors.YELLOW}q.{Colors.RESET} Back to Main Menu")

		try:
			podcast_choice_str = input(f"\n{Colors.BOLD}Enter the number of your choice:{Colors.RESET} ")
			if podcast_choice_str.lower() == 'q':
				print(f"\n{Colors.GREEN}Returning to main menu...{Colors.RESET}")
				time.sleep(1)
				break
			
			podcast_choice = int(podcast_choice_str) - 1
			if not (0 <= podcast_choice < len(podcasts)):
				print(f"{Colors.YELLOW}Invalid choice.{Colors.RESET}")
				continue
		except ValueError:
			print(f"{Colors.YELLOW}Invalid input. Please enter a number or 'q'.{Colors.RESET}")
			continue

		selected_podcast = podcasts[podcast_choice]
		podcast_title = selected_podcast['title']
		podcast_url = selected_podcast['url']
		print(f"\n{Colors.BOLD}You chose:{Colors.RESET} {podcast_title}")

		# --- Episode Selection Loop ---
		while True:
			clear_screen()
			# Get episodes
			episodes = get_episodes_from_rss(podcast_url)
			if not episodes:
				print(f"{Colors.YELLOW}No episodes found for this podcast.{Colors.RESET}")
				break # Go back to the podcast selection loop
			
			# Create a list of episodes with their downloaded status for the menu
			displayed_episodes = []
			podcast_dir_name = sanitize_filename(podcast_title)
			download_dir = os.path.join(SCRIPT_DIR, podcast_dir_name)
			
			for e in episodes:
				file_extension = os.path.splitext(e['url'].split('?')[0])[1].lower()
				sanitized_filename = sanitize_filename(e['title']) + file_extension
				file_path = os.path.join(download_dir, sanitized_filename)
				is_downloaded = os.path.exists(file_path) if os.path.exists(download_dir) else False
				displayed_episodes.append({
					'title': e['title'],
					'url': e['url'],
					'is_downloaded': is_downloaded
				})

			# Present a menu of episodes
			print(f"{Colors.GREEN}-------------------------------------------------------{Colors.RESET}")
			print(f"{Colors.BOLD} Select episodes to download (e.g., 1 3 5, 10-15, or 0{Colors.RESET}")
			print(f"{Colors.RED}     WARNING! Selecting 0 DOWNLOADS ALL EPISODES!{Colors.RESET}")
			print(f"{Colors.GREEN}-------------------------------------------------------\n{Colors.RESET}")
			
			for i, e in enumerate(displayed_episodes):
				if e['is_downloaded']:
					print(f"{Colors.YELLOW}{i + 1}.{Colors.RESET} {e['title']} {Colors.CYAN}(Already downloaded){Colors.RESET}")
				else:
					print(f"{Colors.BLUE}{i + 1}.{Colors.RESET} {e['title']}")
			
			print(f"{Colors.YELLOW}q.{Colors.RESET} Back to Podcast Menu")
			
			episode_choices_str = input(f"\n{Colors.BOLD}Enter the numbers of your choices:{Colors.RESET} ")
			
			if episode_choices_str.lower() == 'q':
				print(f"\n{Colors.GREEN}Returning to podcast menu...{Colors.RESET}")
				break

			episode_choices = episode_choices_str.split()
			episodes_to_download = []
			
			# Process user input for single numbers and ranges
			for choice_str in episode_choices:
				if '-' in choice_str:
					try:
						start_str, end_str = choice_str.split('-')
						start = int(start_str)
						end = int(end_str)
						if start > end:
							print(f"{Colors.YELLOW}Invalid range:{Colors.RESET} Start number ({start}) is greater than end number ({end}). Skipping.")
							continue
						for i in range(start - 1, end):
							if 0 <= i < len(episodes):
								episodes_to_download.append(episodes[i])
							else:
								print(f"{Colors.YELLOW}Invalid number in range:{Colors.RESET} {i + 1} is out of bounds. Skipping.")
					except ValueError:
						print(f"{Colors.YELLOW}Invalid range format:{Colors.RESET} {choice_str}. Skipping.")
				elif choice_str == '0':
					print(f"\n{Colors.BOLD}Preparing to download all episodes...{Colors.RESET}")
					episodes_to_download = episodes
					break
				else:
					try:
						choice_index = int(choice_str) - 1
						if 0 <= choice_index < len(episodes):
							episodes_to_download.append(episodes[choice_index])
						else:
							print(f"{Colors.YELLOW}Invalid choice:{Colors.RESET} {choice_str}. Skipping.")
					except ValueError:
						print(f"{Colors.YELLOW}Invalid input:{Colors.RESET} {choice_str}. Skipping.")
			
			if not episodes_to_download:
				print(f"{Colors.YELLOW}No valid episodes were selected for download.{Colors.RESET}")
				continue
			
			# Create the directory just before downloading
			os.makedirs(download_dir, exist_ok=True)
			print(f"\n{Colors.GREEN}-----------------------------------{Colors.RESET}")
			for selected_episode in episodes_to_download:
				episode_title = selected_episode['title']
				episode_url = selected_episode['url']
				
				# Get the correct file extension from the URL (e.g., .mp3, .m4a)
				# and sanitize the filename
				file_extension = os.path.splitext(episode_url.split('?')[0])[1].lower()
				sanitized_filename = sanitize_filename(episode_title) + file_extension
				file_path = os.path.join(download_dir, sanitized_filename)
				
				# Check if the file already exists to avoid re-downloading
				if os.path.exists(file_path):
					print(f"  {Colors.YELLOW}Skipping:{Colors.RESET} '{os.path.basename(file_path)}' already exists.")
				else:
					download_file(episode_url, file_path, podcast_url)
			
			print(f"\n{Colors.GREEN}-----------------------------------{Colors.RESET}")
			print(f"{Colors.BOLD}Download complete!{Colors.RESET}")
			
			# Ask the user if they want to download another podcast
			print("\nDo you want to download another podcast? ({Colors.BOLD}y{Colors.RESET}/{Colors.BOLD}n{Colors.RESET})".format(Colors=Colors))
			try_again = input(">> ").lower()
			
			if try_again not in ["y", "yes"]:
				print(f"\n{Colors.GREEN}Exiting. Thank you for using Podfetch!{Colors.RESET}")
				time.sleep(2)
				sys.exit(0)
			else:
				break

def select_opml_file_menu(opml_files):
	# Presents a menu to select an OPML file and returns the chosen file path.
	clear_screen()
	print(f"{Colors.GREEN}-----------------------------{Colors.RESET}")
	print(f"{Colors.BOLD} Please select an OPML file:{Colors.RESET}")
	print(f"{Colors.GREEN}-----------------------------\n{Colors.RESET}")
	for i, f in enumerate(opml_files):
		print(f"{Colors.BLUE}{i + 1}.{Colors.RESET} {os.path.basename(f)}")
	print(f"{Colors.YELLOW}q.{Colors.RESET} Quit")
	
	while True:
		try:
			choice_str = input(f"\n{Colors.BOLD}Enter the number of your choice:{Colors.RESET} ")
			if choice_str.lower() == 'q':
				print(f"\n{Colors.GREEN}Exiting. Thank you for using Podfetch!{Colors.RESET}")
				time.sleep(2)
				sys.exit(0)
			
			choice_index = int(choice_str) - 1
			if 0 <= choice_index < len(opml_files):
				return opml_files[choice_index]
			else:
				print(f"{Colors.YELLOW}Invalid choice. Please enter a number from the list or 'q'.{Colors.RESET}")
		except ValueError:
			print(f"{Colors.YELLOW}Invalid input. Please enter a number or 'q'.{Colors.RESET}")

if __name__ == "__main__":
	opml_files = get_opml_files(SCRIPT_DIR)

	if not opml_files:
		print(f"{Colors.YELLOW}Error:{Colors.RESET} No .opml file was found in the script's directory.")
		create_new_file_choice = input(f"Would you like to create a new one? ({Colors.BOLD}y{Colors.RESET}/{Colors.BOLD}n{Colors.RESET}) ".format(Colors=Colors)).lower()
		if create_new_file_choice in ['y', 'yes']:
			OPML_FILE_PATH = create_new_opml_file()
			# If creation failed or user cancelled
			if OPML_FILE_PATH is None or not os.path.exists(OPML_FILE_PATH):
				print(f"{Colors.YELLOW}Failed to create new OPML file. Exiting.{Colors.RESET}")
				sys.exit(1)
		else:
			sys.exit(1)
	else:
		# Default to the first file found
		OPML_FILE_PATH = opml_files[0]

	# --- Main Menu Loop ---
	while True:
		clear_screen()
		
		# Display the ASCII art title at the top of the menu
		print(f"{Colors.CYAN}{Colors.BOLD}{ASCII_ART}{Colors.RESET}")
		print("\n" * 2)
		print(f"{Colors.GREEN}-----------------------------------{Colors.RESET}")
		if OPML_FILE_PATH:
			print(f"{Colors.BOLD}Current OPML file: {os.path.basename(OPML_FILE_PATH)}{Colors.RESET}")
		else:
			print(f"{Colors.BOLD}No OPML file selected.{Colors.RESET}")
		print(f"{Colors.GREEN}-----------------------------------{Colors.RESET}")
		
		# Define the base menu options
		menu_options = {
			'1': download_podcast_menu,
			'2': add_podcast_to_opml,
			'3': remove_podcast_from_opml,
			'4': create_new_opml_file
		}
		
		# Print the base menu options
		print(f"{Colors.BLUE}1.{Colors.RESET} Download existing podcasts")
		print(f"{Colors.BLUE}2.{Colors.RESET} Add a new podcast RSS feed")
		print(f"{Colors.BLUE}3.{Colors.RESET} Remove an existing podcast")
		print(f"{Colors.BLUE}4.{Colors.RESET} Create new OPML file")

		# Check for and add the conditional option
		opml_files = get_opml_files(SCRIPT_DIR)
		if len(opml_files) > 1:
			print(f"{Colors.BLUE}5.{Colors.RESET} Select a different OPML file")
			menu_options['5'] = lambda: select_opml_file_menu(opml_files)
		
		print(f"{Colors.YELLOW}q.{Colors.RESET} Quit")
		
		main_choice = input(f"\n{Colors.BOLD}Enter your choice:{Colors.RESET} ").lower()
		
		if main_choice == 'q':
			print(f"\n{Colors.GREEN}Exiting. Thank you for using Podfetch!{Colors.RESET}")
			time.sleep(1)
			sys.exit(0)
		
		if main_choice in menu_options:
			# Need to handle the return value for the functions that return a new path
			action = menu_options[main_choice]
			if main_choice in ['1', '2', '3']:
				action_result = action(OPML_FILE_PATH)
			else:
				action_result = action()
			
			# Handle return values from functions that might change the OPML_FILE_PATH
			if main_choice in ['4', '5'] and action_result:
				OPML_FILE_PATH = action_result
		else:
			print(f"{Colors.YELLOW}Invalid choice. Please try again.{Colors.RESET}")
			time.sleep(2)
