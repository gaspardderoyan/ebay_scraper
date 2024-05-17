import csv
import sys
import requests
import re
from bs4 import BeautifulSoup
import os

def main():

    # Get the seller
    seller = get_ebay_seller()

    folder_exists(seller)



    ids = get_all_identifiers(seller, start_page= 49,item_per_page= 72)
    save_dicts_as_csv(ids, seller)

    print(ids)

def get_ebay_seller():
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name: ")

    return seller

def get_identifier(url):
    ids = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    items = soup.find_all('img', class_='portrait no-scaling zoom')
    for item in items:
        # get the src attribute of the image tag
        src = item.get('src')
        # apply regex to transform url
        src = replace_image_url(src)

        # find the closest parent dif with the aria-label attribute
        parent_div = item.find_parent('div', class_='str-item-card__header')
        aria_label = parent_div.find('div', role='button').get('aria-label')
        aria_label = re.sub(r' : Quick view', '', aria_label)

        # construct the dict and append to the list 
        item_dict = {'id': src, 'name': aria_label}
        ids.append(item_dict)
        
        print(f"{item_dict}\n")

    return ids

def get_all_identifiers(seller, start_page= 1, item_per_page= 200):
    
    page = start_page
    ids_list = []
    temp_ids = []
    keep_going = True
    while keep_going == True:
        print(f"Get identifiers in page {page}...")
        url = f"https://www.ebay.com/str/{seller}?rt=nc&_pgn={page}&_ipg={item_per_page}"
        ids = get_identifier(url)
        if ids == temp_ids: # check if last page was reached, ie. items are the same
            keep_going = False
            print("Finished!")
        else:
            page += 1
            temp_ids = ids # store the current page to later compare it 
            ids_list.extend(ids)

    return ids_list

def save_dicts_as_csv(ids_dicts, seller):
    keys = ['id', 'name']

    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(ids_dicts)

def replace_image_url(url):
    url = re.sub(r'thumbs/', '', url)
    url = re.sub(r's-l300.\w{1,5}', 's-l1600.jpg', url)

    return url

def folder_exists(seller):
    current_dir = os.getcwd()
    folder_path = os.path.join(current_dir, seller)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{seller}' created.")
        return False
    else:
        print(f"Folder '{seller}' already exists.")
        return True

if __name__ == "__main__":
    main()
