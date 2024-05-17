import csv
import sys
import requests
import re
from bs4 import BeautifulSoup
import os

def main():

    # Get the seller
    seller = get_ebay_seller()

    # Check if the folder exsits, creates it if not
    folder_exists(seller)

    # get the items
    items_list = get_all_identifiers(seller, start_page= 35,item_per_page= 72)

    # # save them
    save_dicts_as_csv(items_list, seller)

    items_list = read_from_csv(seller)
    count_items_in_page(items_list)


def get_ebay_seller():
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name: ")

    return seller

def get_image_urls(page_url):
    # empty list to store dicts for each item
    items_dict = []

    # get content from a page
    response = requests.get(page_url)
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
        item_dict = {'url': src, 'name': aria_label}
        items_dict.append(item_dict)
        

    return items_dict

def get_all_identifiers(seller, start_page= 1, item_per_page= 200):
    
    page = start_page
    items_list = []
    previous_urls = [] # list to store previous items
    keep_going = True
    while keep_going is True:
        print(f"Get identifiers in page {page}...")
        page_url = f"https://www.ebay.com/str/{seller}?rt=nc&_pgn={page}&_ipg={item_per_page}"
        current_items = get_image_urls(page_url) # get the products urls and name

        # extract current urls
        current_urls = [item['url'] for item in current_items]


        if current_urls == previous_urls: # check if last page was reached, ie. items are the same
            keep_going = False
            print("Finished!")
        else:
            for item in current_items:
                item['page'] = page # add the page number to each item dict
            page += 1
            previous_urls = current_urls # store the current page to later compare it 
            items_list.extend(current_items)

    return items_list

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

def save_dicts_as_csv(ids_dicts, seller):
    keys = ['url', 'name', 'page']

    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(ids_dicts)

    print(f"{filename} was saved!")

def read_from_csv(seller):
    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def count_items_in_page(items_list):
    # empty dict to hold the counts
    page_counts = {}

    # iterate over list of dictionaries
    for item in items_list:
        page = item['page']
        if page in page_counts:
            page_counts[page] += 1
        else:
            page_counts[page] = 1

    # print the counts per page
    for page, count in page_counts.items():
        print(f"Page {page} has {count} items.\n")

if __name__ == "__main__":
    main()
