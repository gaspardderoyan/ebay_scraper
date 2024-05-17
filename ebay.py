import requests
from bs4 import BeautifulSoup
import os
import csv
import sys

def main():

    # Get the seller
    seller = 'garbagearchive'
    # seller = get_ebay_seller()

    ids = get_all_identifiers(seller, start_page= 49,item_per_page= 72, method= 'image')

    print(ids)

def get_ebay_seller():
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name: ")

    return seller

def get_identifier(url, method= 'image'):
    ids = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    if method == 'identifier':
        items = soup.find_all('article')
        for item in items:
            src = item.get('data-testid')
            if src:
                ids.append(src.removeprefix('ig-'))
    elif method == 'image':
        items = soup.find_all('img', class_='portrait no-scaling zoom')
        for item in items:
            src = item.get('src')
            ids.append(src)
            print(f"{src}\n\n")
    else:
        sys.exit("method name not set")

    return ids

def get_all_identifiers(seller, start_page= 1, item_per_page= 200, method= 'image'):
    
    page = start_page
    ids_list = []
    temp_ids = []
    keep_going = True
    while keep_going == True:
        print(f"Get identifiers in page {page}...")
        url = f"https://www.ebay.com/str/{seller}?rt=nc&_pgn={page}&_ipg={item_per_page}"
        ids = get_identifier(url, method= method)
        if ids == temp_ids: # check if last page was reached, ie. items are the same
            keep_going = False
            print("Finished!")
        else:
            page += 1
            temps_ids = ids # store the current page to later compare it 
            ids_list.extend(ids)

    # Save as CSV
    with open(f'{seller}_ids.csv', 'w') as file:
        writer = csv.writer(file)
        for item in ids_list:
            writer.writerow([item])

    return ids_list




def get_products_urls(ids):
    ...

if __name__ == "__main__":
    main()
