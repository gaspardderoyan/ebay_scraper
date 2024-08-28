import csv
import sys
import requests
import re
from bs4 import BeautifulSoup
import os
import signal

# Global flag to detect if Ctrl+C was pressed
interrupted = False

def main():
    """
    Main function to orchestrate the scraping process.
    It checks for existing data, starts scraping from the correct page, 
    and saves the results.
    """
    # Handle Ctrl+C signal
    signal.signal(signal.SIGINT, handle_interrupt)

    # Get the seller
    seller = get_ebay_seller()

    # Load existing data if available, and determine the start page
    items_list, start_page = load_data(seller)

    try:
        # Scrape items from eBay
        items_list = get_all_articles(seller, start_page=start_page, item_per_page=48, items_list=items_list)
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        # Always save data before exiting
        save_dicts_as_csv(items_list, seller)

def handle_interrupt(signum, frame):
    """
    Handle the SIGINT (Ctrl+C) signal and set the interrupted flag.
    """
    global interrupted
    interrupted = True
    print("\nInterrupt received, saving data...")

def get_ebay_seller():
    """
    Retrieve the eBay seller's name either from command line arguments or user input.
    
    Returns:
        seller (str): The eBay seller's name.
    """
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name: ")
    return seller

def load_data(seller):
    """
    Load existing data for the given seller and determine the starting page.
    
    Args:
        seller (str): The eBay seller's name.
    
    Returns:
        tuple: A list of existing items and the starting page number.
    """
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

def get_articles_info(page_url, fallback=False):
    """
    Fetch article information from the given eBay page URL.
    
    Args:
        page_url (str): The URL of the eBay page to scrape.
        fallback (bool): Whether to use the fallback method for scraping.
    
    Returns:
        list: A list of dictionaries containing article information.
    """
    articles_info = []

    try:
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        if fallback:
            articles = soup.find_all('article', class_='str-item-card')
            print(f"Found {len(articles)} articles using fallback method")
        else:
            articles = soup.find_all('article', class_='str-item-card')
            print(f"Found {len(articles)} articles")

        for article in articles:
            try:
                data_testid = article.get('data-testid')

                if fallback:
                    button_div = article.find('div', class_='str-quickview-button')
                    title = None
                    if button_div:
                        aria_label = button_div.get('aria-label')
                        title = re.sub(r' : Quick view', '', aria_label)
                else:
                    title_span = article.find('span', class_='str-item-card__property-title')
                    title = title_span.get_text(strip=True) if title_span else None

                img_tag = article.find('img')
                src = replace_image_url(img_tag.get('src')) if img_tag else None

                article_info = {'id': data_testid, 'url': src, 'name': title}
                articles_info.append(article_info)
            except Exception as e:
                print(f"Error processing article: {e}")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return articles_info

def get_all_articles(seller, start_page=1, item_per_page=48, items_list=[]):
    """
    Scrape all articles for the given seller, starting from a specific page.
    
    Args:
        seller (str): The eBay seller's name.
        start_page (int): The page number to start scraping from.
        item_per_page (int): The number of items per page.
        items_list (list): The list to store the scraped items.
    
    Returns:
        list: An updated list of all scraped items.
    """
    global interrupted
    page = start_page
    previous_urls = []
    keep_going = True
    use_fallback = False

    while keep_going and not interrupted:
        print(f"Get identifiers on page {page}...")
        if not use_fallback:
            page_url = f"https://www.ebay.com/usr/{seller}"
            current_items = get_articles_info(page_url)
        else:
            page_url = f"https://www.ebay.com/str/{seller}?_sop=15&_ipg={item_per_page}&_pgn={page}"
            current_items = get_articles_info(page_url, fallback=True)

        # Switch to fallback method if no items found and it's the first try
        if not current_items and not use_fallback:
            print("Switching to fallback method...")
            use_fallback = True
            continue

        current_urls = [item['url'] for item in current_items]

        if current_urls == previous_urls:
            keep_going = False
            print("Finished!")
        else:
            for item in current_items:
                item['page'] = page
            page += 1
            previous_urls = current_urls
            items_list.extend(current_items)

    if interrupted:
        print("Script interrupted, saving data...")

    return items_list

def replace_image_url(url):
    """
    Modify the image URL to point to a higher resolution image.
    
    Args:
        url (str): The original image URL.
    
    Returns:
        str: The modified image URL.
    """
    url = re.sub(r'thumbs/', '', url)
    url = re.sub(r's-l300.\w{1,5}', 's-l1600.jpg', url)
    return url

def save_dicts_as_csv(ids_dicts, seller):
    """
    Save a list of dictionaries to a CSV file.
    
    Args:
        ids_dicts (list): List of dictionaries containing article information.
        seller (str): The eBay seller's name.
    """
    keys = ['id', 'url', 'name', 'page']
    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(ids_dicts)

    print(f"{filename} was saved!")

def read_from_csv(seller):
    """
    Read a CSV file and return its contents as a list of dictionaries.
    
    Args:
        seller (str): The eBay seller's name.
    
    Returns:
        list: A list of dictionaries containing the CSV contents.
    """
    filename = os.path.join(seller, 'file_info_list' + '.csv')

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def count_items_in_page(items_list):
    """
    Count the number of items per page and print the results.
    
    Args:
        items_list (list): The list of items to count.
    """
    page_counts = {}

    for item in items_list:
        page = item['page']
        if page in page_counts:
            page_counts[page] += 1
        else:
            page_counts[page] = 1

    for page, count in page_counts.items():
        print(f"Page {page} has {count} items.\n")

if __name__ == "__main__":
    main()