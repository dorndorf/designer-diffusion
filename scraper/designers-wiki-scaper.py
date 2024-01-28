import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
import os
import re
import time

# Constants for retrying downloads
MAX_RETRY_COUNT = 3
RETRY_DELAY = 2

# Define a custom user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"


def sanitize_filename(name):
    sanitized_name = re.sub(r'[\\/*?:"<>|]', '', name)
    sanitized_name = re.sub(r'\.(?!(jpg|jpeg|png)\b)', '_', sanitized_name)
    return sanitized_name

def is_valid_image(file_name):
    return file_name.lower().endswith(('.jpg', '.jpeg', '.png'))

def is_image_large_enough(file_path, min_size=100):
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            return min(width, height) >= min_size
    except:
        return False

def download_image(image_url, folder_name, image_counter):
    for retry_count in range(MAX_RETRY_COUNT):
        try:
            if not is_valid_image(image_url):
                print(f"Skipped non-JPG/JPEG/PNG file: {image_url}")
                return
            
            # Skip downloading files named "Wikipedia.png"
            if "Wikipedia.png" in image_url:
                print("Skipped file: Wikipedia.png")
                return

            print(f"Attempting to download: {image_url}")


            headers = {
                "User-Agent": USER_AGENT,
            }

            img_data = requests.get(image_url, headers=headers).content

            file_extension = image_url.split('.')[-1]
            file_name = f"image{image_counter}.{file_extension}"
            file_path = os.path.join(folder_name, file_name)

            with open(file_path, 'wb') as file:
                file.write(img_data)

            if is_image_valid(file_path) and is_image_large_enough(file_path):
                print(f'Downloaded and verified {file_path}')
            else:
                print(f'Downloaded file is either corrupted or too small: {file_path}')
                os.remove(file_path)

            return 

        except Exception as e:
            print(f"Error downloading {image_url}: {e}")
            if retry_count < MAX_RETRY_COUNT - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"Reached maximum retry attempts for {image_url}. Skipping.")

def is_image_valid(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify() 
        return True
    except:
        return False

def get_high_res_image_url(thumbnail_url):
    file_name = thumbnail_url.split('/')[-1]
    file_name = re.sub(r'\d+px-', '', file_name)
    file_name = file_name.split(':')[1] if ':' in file_name else file_name
    media_viewer_url = f"https://en.wikipedia.org/wiki/File:{file_name}"

    try:
        response = requests.get(media_viewer_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        original_file_link = soup.find('a', class_='internal', href=True)
        if original_file_link:
            high_res_url = 'https:' + original_file_link['href']
            if is_valid_image(high_res_url):
                return high_res_url
    except Exception as e:
        print(f"Error fetching high-res image URL from {media_viewer_url}: {e}")
    return None

def download_images_from_wikipedia(page_url, folder_name):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    image_counter = 0

    for img in images:
        img_url = img['src']
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = 'https://upload.wikimedia.org' + img_url

        high_res_url = get_high_res_image_url(img_url)
        if high_res_url:
            download_image(high_res_url, folder_name, image_counter)
        else:
            print(f"High-res image not found for {img_url}, downloading low-res version.")
            download_image(img_url, folder_name, image_counter)

        image_counter += 1

        time.sleep(2)

with open('../lists/designers.json', 'r') as file:
    designers = json.load(file)

for designer_name, url in designers.items():
    folder_name = sanitize_filename(designer_name)
    folder_name = os.path.join('./images', folder_name)
    download_images_from_wikipedia(url, folder_name)
