import sys
from ebay_old import get_articles_info
import pandas as pd

def print_items_table(items):
    """
    Print the first 10 items in a tabular format using pandas.
    Save the table as a CSV file.
    
    Args:
        items (list): List of dictionaries containing item information.
    """
    # Take the first 10 items
    items_to_display = items[:10]
    
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(items_to_display)
    
    # Ensure all columns are displayed in the console
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    # Print the DataFrame as a table
    print(df)
    
    # Save the DataFrame to a CSV file
    df.to_csv('output_items.csv', index=False)
    print("The first 10 items have been saved to 'output_items.csv'.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_ebay.py <eBay seller page URL>")
        sys.exit(1)
    
    # Get the page URL from the command-line arguments
    page_url = sys.argv[1]
    
    # Fetch the article information
    items = get_articles_info(page_url)
    
    if items:
        print_items_table(items)
    else:
        print("No items found.")

if __name__ == "__main__":
    main()