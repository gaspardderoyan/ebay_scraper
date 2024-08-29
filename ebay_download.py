from concurrent.futures import ThreadPoolExecutor
from ebay import get_ebay_seller
import os
import csv
import requests
from tqdm import tqdm
from functools import partial
import re

def main():

    seller = get_ebay_seller()

    file_info_list = read_from_csv(seller)

    download_all_files(file_info_list, seller)

    

def read_from_csv(seller):
    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def sanitize_filename(filename):
    # Remove any characters that are not alphanumeric, dots, underscores, or spaces
    sanitized = re.sub(r'[^a-zA-Z0-9._\s]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_').replace('/', '_').replace('\\', '_')
    return sanitized
    
def download_file(dict, seller):
    url = dict['url']
    file_name = sanitize_filename(dict['name'])

    # Ensure the file has an extension, default to .jpg if not specified
    if os.path.splitext(file_name)[1] not in ['.jpg', '.jpeg', '.png']:
        file_name += '.jpg'
        
    folder_name = seller
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        save_path = os.path.join(folder_name, file_name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {file_name}")
    except Exception as e:
        print(f"Failed to download {url}. Reason: {e}")

def download_all_files(list_of_dicts, seller):
    with ThreadPoolExecutor(max_workers=10) as executor:
        part_download_file = partial(download_file, seller=seller)
        list(tqdm(executor.map(part_download_file, list_of_dicts), total=len(list_of_dicts), desc="Downloading files"))
    
if __name__ == "__main__":
    main()