import os
import json
import requests
import time
import boto3
import datetime
import logging
import numpy as np
from bs4 import BeautifulSoup
from utilities import load_pickle, load_proxy_details
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def scrape_categories(partitions: list, proxies: dict, user_agents: dict) -> dict:
    """Scrape each product from a given list of categories to get price per unit,
    price per weight or quantity, product ID, and its category hierarchy.

    Args:
        partitions (list): List containing Tesco grocery shopping categories and page number ranges
        proxies (dict): Proxy details to use with GET requests
        user_agents (dict): Dictionary of common user agents to use with GET requests

    Returns:
        prod_dict (dict): Dictionary containing details of products
    """
    base_URL = "https://www.tesco.com/groceries/en-GB/shop"
    main_prod_dict = {}
    user_agent_idx = np.random.randint(low=0, high=len(user_agents)-1)
    
    for partition_dict in partitions:
        for page_num in range(partition_dict["start_index"], partition_dict["end_index"]+1):
            URL = f"{base_URL}/{partition_dict['category']}/all?page={page_num}&count=48"
            page = requests.get(
                URL,
                headers={'User-agent': user_agents[user_agent_idx]['useragent']},
                proxies=proxies,
                timeout=30
            )
            soup = BeautifulSoup(page.content, "html.parser")
            
            product_list = soup.find_all("li", class_="product-list--list-item")
            
            prod_dict = {}
            for idx, prod in enumerate(product_list, 0):
                prod_name = prod.find('span', class_="styled__Text-sc-1xbujuz-1 ldbwMG beans-link__text").get_text()
                prod_id = int(prod.find('div', class_="styles__StyledTiledContent-dvv1wj-3 bcglTg")['data-auto-id'])
            
                try:
                    prod_price_per_unit = float(
                        (prod
                         .find('p', class_="styled__StyledHeading-sc-119w3hf-2 jWPEtj styled__Text-sc-8qlq5b-1 lnaeiZ beans-price__text")
                         .get_text()
                         .replace('£', '')
                         .replace(',', '')
                        )
                    )
                except AttributeError:
                    prod_price_per_unit = np.nan
            
                try:
                    prod_price_per_weight_quant = float(
                        (prod
                         .find('p', class_="styled__StyledFootnote-sc-119w3hf-7 icrlVF styled__Subtext-sc-8qlq5b-2 bNJmdc beans-price__subtext")
                         .get_text()
                         .split('/')[0]
                         .replace('£', '')
                         .replace(',', '')
                        )
                    )
                except AttributeError:
                    prod_price_per_weight_quant = np.nan
            
                try:
                    prod_weight_quant_unit = (
                        prod
                        .find('p', class_="styled__StyledFootnote-sc-119w3hf-7 icrlVF styled__Subtext-sc-8qlq5b-2 bNJmdc beans-price__subtext")
                        .get_text()
                        .split('/')[-1]
                    )
                except AttributeError:
                    prod_weight_quant_unit = np.nan
            
                try:
                    offer = (
                        prod
                         .find('div', class_='styles__StyledPromotionsOfferContent-sc-1vdpoop-1 cQQRuD')
                         .find('span', class_='offer-text')
                         .get_text()
                    )
                except AttributeError:
                    offer = np.nan
            
                cat_dict = {}
                for ele in prod.find_all('a', class_="styled__Anchor-sc-1xbujuz-0 cFilde beans-link__anchor"):
                    if "/groceries/en-GB/shop/" in ele['href']:
                        for idx, cat in enumerate(ele['href'].split('/')[4:], 1):
                            cat_dict[f"category_{idx}"] = cat
            
                prod_dict[prod_id] = {
                    'name': prod_name,
                    'price_per_unit': prod_price_per_unit,
                    'price_per_weight_quant': prod_price_per_weight_quant,
                    'weight_quant_unit': prod_weight_quant_unit,
                    'offer': offer
                }
                prod_dict[prod_id].update(cat_dict)

            main_prod_dict.update(prod_dict)
            print(f"Finished scraping page {page_num-partition_dict['start_index']+1} out of {partition_dict['end_index']-partition_dict['start_index']+1} for {' '.join(partition_dict['category'].split('-'))} category")
            print(f"Scraped {len(prod_dict)} products")

            time.sleep(np.random.uniform(low=8, high=12))

    return main_prod_dict


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

    # Scrape products in partition categories
    prod_dict = scrape_categories(event, proxy_dict, user_agents)

    # Save to S3 since the payload is too large to flow through step function
    curr_date = datetime.datetime.now().strftime("%Y-%m-%d")
    key = f'raw_data/{curr_date}_partition_{np.random.randint(1e12, 2e12, 1)[0]}.json'
    s3object = s3.Object(BUCKET, key)
    s3object.put(
        Body=(bytes(json.dumps(prod_dict).encode('UTF-8')))
    )

    return {
        'body': {
            'bucket': BUCKET,
            'key': key
        }
    }
