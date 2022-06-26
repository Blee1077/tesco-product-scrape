import os
import json
import re
import requests
import time
import boto3
import datetime
import logging
import numpy as np
from bs4 import BeautifulSoup
from utilities import load_json, load_pickle, load_proxy_details
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def scrape_products(
    partition: list, proxies: dict, master_prods_dict: dict, user_agents: dict
    ) -> dict:
    """Scrape each product from a given list of categories to get price per unit,
    price per weight or quantity, product ID, and its category hierarchy.

    Args:
        proxies (dict): Proxy details to use with GET requests

    Returns:
        prod_dict (dict): Dictionary containing details of products
    """
    base_URL = "https://www.tesco.com/groceries/en-GB/products"
    prod_dict = {}
    for idx, prod_id in enumerate(partition, 1):
        URL = f"{base_URL}/{prod_id}"
        page = requests.get(
            URL,
            headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'},
            proxies=proxies,
            timeout=30
        )
        soup = BeautifulSoup(page.content, "html.parser")

        # If can't get product name then it's probably a dead page
        # Remove from master products table
        try:
            prod_name = soup.find('h1', class_="product-details-tile__title").get_text()
        except:
            master_prods_dict.pop(prod_id, None)
            continue

        try:
            prod_price_per_unit = float(
                (soup
                 .find('div', class_="price-per-sellable-unit price-per-sellable-unit--price price-per-sellable-unit--price-per-item")
                 .find('span', class_="value")
                 .get_text()
                 .replace(',', '')
                )
            )
        except AttributeError:
            prod_price_per_unit = np.nan

        try:
            prod_price_per_weight_quant = float(
                (soup
                 .find('div', class_="price-per-quantity-weight")
                 .find('span', class_="value")
                 .get_text()
                 .replace(',', '')
                )
            )
        except AttributeError:
            prod_price_per_weight_quant = np.nan

        try:
            prod_weight_quant_unit = (
                soup
                .find('div', class_="price-per-quantity-weight")
                .find('span', class_="weight")
                .get_text().split('/')[-1]
            )
        except AttributeError:
            prod_weight_quant_unit = np.nan

        try:
            offer = (
                soup
                 .find('li', class_='product-promotion')
                 .find('span', class_='offer-text')
                 .get_text()
            )
        except AttributeError:
            offer = None

        # Get category and subcategories of product
        try:
            cat_str = re.search(
                r'(?<={}).*?(?={})'.format('"restOfShelfUrl":', '"template"'),
                soup.find('body', {'data-app-name': "prd"}).get('data-redux-state').strip()
            ).group(0)
        except:
            cat_str = None

        cat_dict = {}
        replace_list = ["'", "+", ",", '"',]
        if cat_str:
            for cat_idx, cat in enumerate(cat_str.split('/')[2:], 1):
                if cat_idx == 4:
                    for s in replace_list:
                        cat = cat.replace(s, '')
                cat_dict[f"category_{cat_idx}"] = cat

        prod_dict[prod_id] = {
            'name': prod_name,
            'price_per_unit': prod_price_per_unit,
            'price_per_weight_quant': prod_price_per_weight_quant,
            'weight_quant_unit': prod_weight_quant_unit,
            'offer': offer
        }
        prod_dict[prod_id].update(cat_dict)
        logging.info(f"Finished scraping product {idx} out of {len(partition)}")

        time.sleep(np.random.uniform(low=8, high=12))

    return prod_dict, master_prods_dict


def lambda_handler(event, context):
    # Bucket containing project files
    BUCKET = os.environ['BUCKET_NAME']

    # Get SOCKS5 proxy details
    proxy_dict, _ = load_proxy_details(BUCKET, os.environ['PROXY_DETAILS_KEY'])

    # Get list of user agents
    user_agents = load_pickle(
        bucket=BUCKET,
        key=os.environ['USER_AGENTS_KEY']
    )

    # Load JSON of master products table
    master_prod_key = "master_data/all_product_ids_names.json"
    master_prods_dict = load_json(BUCKET, master_prod_key)
    num_prods_in_master = len(master_prods_dict)

    # Scrape products in partition categories, remove dead products from master products table if encountered
    prod_dict, master_prods_dict = scrape_products(event["partition"], proxy_dict, master_prods_dict, user_agents)
    logging.info(f"Successfully scraped {len(prod_dict)} products out of {len(event['partition'])}")
    logging.info(f"Removed {num_prods_in_master - len(master_prods_dict)} products from master products table since their page can't be loaded")

    # Save to S3 since the payload is too large to flow through step function
    curr_date = datetime.datetime.now().strftime("%Y-%m-%d")
    key = f'raw_data/{curr_date}_partition_{np.random.randint(2e12, 3e12, 1)[0]}.json'
    s3object = s3.Object(BUCKET, key)
    s3object.put(
        Body=(bytes(json.dumps(prod_dict).encode('UTF-8')))
    )

    # Save updated master products table if dead products found
    if num_prods_in_master != len(master_prods_dict):
        s3object = s3.Object(
            BUCKET, master_prod_key
        )
        s3object.put(
            Body=(bytes(json.dumps(master_prods_dict).encode('UTF-8')))
        )
        logging.info(f"Saved updated master products table to S3")

    return {
        'body': {
            'bucket': BUCKET,
            'key': key
        }
    }
