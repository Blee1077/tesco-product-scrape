import os
import requests
import math
import datetime
import logging
from bs4 import BeautifulSoup
from utilities import load_proxy_details
logging.getLogger().setLevel(logging.INFO)

def get_shopping_categories(proxies: dict) -> list:
    """Gets the grocery shopping categories from Tesco.

    Args:
        proxy_details (dict): Dictionary containing SOCK5 proxy details

    Returns:
        List of Tesco grocery shopping categories
    """
    URL = "https://www.tesco.com/groceries/en-GB/shop"
    page = requests.get(
        URL,
        headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'},
        proxies=proxies,
        timeout=120
    )
    soup = BeautifulSoup(page.content, "html.parser")

    grocery_categories = []
    for link in soup.findAll('a'):
        if '/groceries/en-GB/shop/' in link.get('href'):
            grocery_categories.append(link.get('href').split('/')[-1].split('?')[0])

    grocery_categories = [cat for cat in grocery_categories if (len(cat) > 0) and ('inspiration' not in cat)]
    excluded_categories = [
        'easter',
        'baby',
        'health-and-beauty',
        'pets',
        'household',
        'home-and-ents'
    ]
    grocery_categories = [cat for cat in grocery_categories if cat not in excluded_categories]

    return grocery_categories


def get_page_num_per_category(grocery_categories: list, proxies: dict) -> dict:
    """Calculates the number of pages per shopping category on Tesco assuming 48 items is listed per page.

    Args:
        grocery_categories (list): List of Tesco grocery shopping categories
        proxies (dict): Dictionary containing SOCK5 proxy details

    Returns:
        Dictionary containing category as keys and number of pages as values
    """
    groc_cat_pages = {}
    groc_cat_num_items = {}
    for groc_cat in grocery_categories:
        URL = f"https://www.tesco.com/groceries/en-GB/shop/{groc_cat}/all?count=48"
        page = requests.get(
            URL,
            headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'},
            proxies=proxies,
            timeout=120
        )
        soup = BeautifulSoup(page.content, "html.parser")
        
        num_items = int(soup.find('div', class_='pagination__items-displayed').get_text().split(' ')[5])
        max_pages = math.ceil(num_items / 48)
        groc_cat_pages[groc_cat] = max_pages
        groc_cat_num_items[groc_cat] = num_items

    return groc_cat_pages, groc_cat_num_items


def partition_list(groc_cat_pages: dict, pages_per_partition: int) -> list:
    """This code partitions the grocery cateory pages into a lists with each containing pages_per_partition number of pages.
    I don't know how or why this works but it works exactly as it needs to. Don't touch it.
    
    Args:
        groc_cat_pages (dict): Dictionary which map grocery category to how many pages it has
        pages_per_partition (int): Number of pages in each partition

    Returns:
        List of lists
    """
    counts = 0
    main_lst = []
    for idx, (cat, pages) in enumerate(groc_cat_pages.items()):
        if idx == 0:
            part_list = []
        cat_pages = pages
        lst1 = {'category': cat, 'end_index': cat_pages}
        
        while (pages > 1):
            pages -= 1
            counts += 1
            if counts == pages_per_partition:
                lst1['start_index'] = pages
                part_list.append(lst1)
                main_lst.append(part_list)
                
                counts = 0
                pages -= 1
                lst1 = {'category': cat, 'end_index': pages}
                part_list = []
                
        if pages == 0:
            continue
            
        lst1['start_index'] = pages
        part_list.append(lst1)
        
        if idx == len(groc_cat_pages)-1:
            main_lst.append(part_list)
            
    return main_lst


def lambda_handler(event, context):
    # Load in proxy details

    proxies, exp_date = load_proxy_details(os.environ['BUCKET_NAME'], os.environ['PROXY_DETAILS_KEY'])
    logging.info("Loaded in SOCK5 proxy details")
    
    # Check proxy is still valid to use
    exp_date = datetime.datetime.strptime(exp_date, '%Y-%m-%d').date()
    curr_date = datetime.datetime.today().date()
    assert(curr_date <= exp_date), "Proxy has expired. Renew proxy for continued functionality."
    
    days_remaining = (exp_date - curr_date).days
    if days_remaining <= 14:
        logging.warning(f"Proxy is valid for {days_remaining} days before expiring.")
        
    # Get Tesco shopping categories
    grocery_categories = get_shopping_categories(proxies)
    logging.info(f"Scraped Tesco grocery categories: {grocery_categories}")
    
    # Check if in test mode
    if 'test' in event:
        grocery_categories = grocery_categories[:event['test']]
        print(f"Test mode. Restricting to categories: {grocery_categories}")

    # Get number of pages in each category
    groc_cat_pages, groc_cat_num_items = get_page_num_per_category(grocery_categories, proxies)
    logging.info(f"Number of pages for each category: {groc_cat_pages}")

    # Partition categories lists that sum to a total of x pages
    partitions = partition_list(groc_cat_pages, event["pages_per_partition"])
    logging.info(f"Created {len(partitions)} partitions containing {event['pages_per_partition']} total pages each")

    return {
        'statusCode': 200,
        'body': {
            "partitions": partitions,
            "category_item_counts": groc_cat_num_items
        }
    }
