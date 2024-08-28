import csv
import sys
import requests
import re
from bs4 import BeautifulSoup
import os

def main():
    """MAIN"""

    # Get the seller
    seller = get_ebay_seller()

    # Check if the folder exsits, creates it if not
    # Check if csv exists
    # If so, loads it, and set the start page to the last page inside of it
    # Else, start at 1
    items_list, start_page = load_data(seller)

    # Get the items
    items_list = get_all_articles(seller, start_page= start_page,item_per_page= 48, items_list= items_list)

    # Save them
    save_dicts_as_csv(items_list, seller)


def get_ebay_seller():
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name: ")

    return seller

def load_data(seller):
    current_dir = os.getcwd()
    folder_path = os.path.join(current_dir, seller)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{seller}' created.")
    else:
        print(f"Folder '{seller}' already exists.")

    filepath = os.path.join(current_dir, seller, 'file_info_list' + '.csv')
    if os.path.exists(filepath):
        items_list = read_from_csv(seller)
        try:
            start_page = max(int(item['page']) for item in items_list)
            print(f"Data record was loaded, starting at page {start_page}.")
        except ValueError:
            start_page = 1
            print("The data was empty")
    else:
        items_list = []
        start_page = 1
        print("No data was found, starting from scratch.")

    return items_list, start_page

def get_articles_info(page_url):
    # List to store dicts for each article
    articles_info = []

    try:
        # Get content from a page
        response = requests.get(page_url)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all article elements
        articles = soup.find_all('article', class_='str-item-card')
        print(f"Found {len(articles)} articles")

        for article in articles:
            try:
                # Get the data-testid attribute of the article
                data_testid = article.get('data-testid')

                # Find the div with the role 'button' to get the aria-label attribute
                button_div = article.find('div', class_='str-quickview-button')
                if button_div:
                    aria_label = button_div.get('aria-label')
                    aria_label = re.sub(r' : Quick view', '', aria_label)
                else:
                    aria_label = None

                # Find the img tag to get the src attribute
                img_tag = article.find('img')
                if img_tag:
                    src = img_tag.get('src')
                    src = replace_image_url(src)
                else:
                    src = None

                # Construct the dict and append to the list
                article_info = {'id': data_testid, 'url': src, 'name': aria_label}
                articles_info.append(article_info)
            except Exception as e:
                print(f"Error processing article: {e}")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return articles_info

def get_all_articles(seller, start_page= 1, item_per_page= 48, items_list = []):
    
    page = start_page
    
    previous_urls = [] # list to store previous items
    keep_going = True
    while keep_going is True:
        print(f"Get identifiers in page {page}...")
        page_url = f"https://www.ebay.com/str/{seller}?_sop=15&_ipg={item_per_page}&_pgn={page}"
        current_items = get_articles_info(page_url) # get the products urls and name

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

def save_dicts_as_csv(ids_dicts, seller):
    keys = ['id', 'url', 'name', 'page']

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
