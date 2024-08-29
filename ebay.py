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

    # Get the seller and keyword
    seller, keyword = get_ebay_seller_and_keyword()

    # Determine folder name
    folder_name = seller if seller else keyword.replace(' ', '_')

    # Load existing data if available, and determine the start page
    items_list, start_page = load_data(folder_name)  # Use a default folder name if no seller

    try:
        # Scrape items from eBay
        items_list = get_all_articles(seller, keyword, start_page=start_page, items_list=items_list)
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
 # Only save data if items were actually scraped
        if items_list:
            save_dicts_as_csv(items_list, folder_name)
        else:
            print("No data was created or loaded. Exiting normally.")

def handle_interrupt(signum, frame):
    """
    Handle the SIGINT (Ctrl+C) signal and set the interrupted flag.
    """
    global interrupted
    interrupted = True
    print("\nInterrupt received, saving data...")

def get_ebay_seller_and_keyword():
    """
    Retrieve the eBay seller's name and keyword(s) either from command line arguments or user input.
    
    Returns:
        seller (str): The eBay seller's name (can be an empty string).
        keyword (str): The keyword(s) to search for on eBay.
    """
    try:
        seller = sys.argv[1]
    except IndexError:
        seller = input("Enter the seller's name (leave blank for general search): ")

    try:
        keyword = sys.argv[2]
    except IndexError:
        keyword = input("Enter the search keyword(s), or leave blank: ")

    return seller, keyword

def load_data(folder_name):
    """
    Load existing data for the given folder and determine the starting page.
    
    Args:
        folder_name (str): The folder name to store data.
    
    Returns:
        tuple: A list of existing items and the starting page number.
    """
    current_dir = os.getcwd()
    folder_path = os.path.join(current_dir, folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_name}' created.")
    else:
        print(f"Folder '{folder_name}' already exists.")

    filepath = os.path.join(current_dir, folder_name, 'file_info_list' + '.csv')
    if os.path.exists(filepath):
        items_list = read_from_csv(folder_name)
        try:
            start_page = max(int(item['page']) for item in items_list) + 1
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

        articles = soup.find_all('li', class_='s-item')
        print(f"Found {len(articles)} articles using fallback method")

        for article in articles:
            try:
                # Fallback scraping method
                item_id = None
                href_tag = article.find('a', href=True)
                if href_tag:
                    # Extract item ID from the href attribute
                    href = href_tag['href']
                    item_id = href.split('/itm/')[1].split('?')[0] if '/itm/' in href else None

                title_tag = article.find('div', class_='s-item__title')
                title = title_tag.get_text(strip=True) if title_tag else None

                img_tag = article.find('img')
                src = replace_image_url(img_tag.get('src')) if img_tag else None

                article_info = {'id': item_id, 'url': src, 'name': title}

                if article_info['id'] == '123456':
                    # print(f"Skipping item with id 123456")
                    continue

                if article_info['id']:
                    articles_info.append(article_info)
            except Exception as e:
                print(f"Error processing article: {e}")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return articles_info

def get_all_articles(seller, keyword, start_page=1,  items_list=[]):
    """
    Scrape all articles for the given seller and keyword, starting from a specific page.
    
    Args:
        seller (str): The eBay seller's name (can be empty for a general search).
        keyword (str): The keyword(s) to search for on eBay (can be empty).
        start_page (int): The page number to start scraping from.
        items_list (list): The list to store the scraped items.
    
    Returns:
        list: An updated list of all scraped items.
    """
    global interrupted
    page = start_page
    previous_urls = set()
    existing_ids = {item['id'] for item in items_list}  # Collect existing IDs from loaded data
    keep_going = True

    # Prepare keyword for URL if provided
    keyword = '+'.join(keyword.split()) if keyword else None

    while keep_going and not interrupted:
        print(f"Get identifiers on page {page}...")
        if seller and keyword:
            page_url = f"https://www.ebay.com/sch/i.html?_ssn={seller}&_nkw={keyword}_pgn={page}"
        elif seller:
            page_url = f"https://www.ebay.com/sch/i.html?_ssn={seller}&_pgn={page}"
        elif keyword:
            page_url = f"https://www.ebay.com/sch/i.html?_nkw={keyword}&_pgn={page}"
        else:
            page_url = f"https://www.ebay.com/sch/i.html?_pgn={page}"

        print(f"Scraping URL: {page_url}")
        current_items = get_articles_info(page_url)

        # Debug print
        print(f"Found {len(current_items)} new items on page {page}")

        if not current_items:
            print("No items found on this page. Stopping scraping.")
            keep_going = False
            break

        # Check if any new items were found
        new_items = [item for item in current_items if item['id'] not in existing_ids]
        
        if not new_items:
            print("All items on this page are already in the dataset. Stopping scraping.")
            keep_going = False
            break

        # Add new items to the list and update existing_ids
        for item in new_items:
            item['page'] = page
            existing_ids.add(item['id'])
        
        items_list.extend(new_items)
        page += 1

        # Debug print
        print(f"Added {len(new_items)} new items. Total items: {len(items_list)}")

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
    # url = re.sub(r's-l300.\w{1,5}', 's-l1600.jpg', url)
    url = re.sub(r's-l\d+\.jpg', 's-l1600.jpg', url)
    return url

def save_dicts_as_csv(ids_dicts, folder_name):
    """
    Save a list of dictionaries to a CSV file.
    
    Args:
        ids_dicts (list): List of dictionaries containing article information.
        folder_name (str): The folder name to store the CSV.
    """
    keys = ['id', 'url', 'name', 'page']
    filename = os.path.join(folder_name, 'file_info_list' + '.csv')

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
