import os
import json
import boto3
import logging
import math
import botocore
from utilities import load_json
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    # Load CSV of combined data
    combined_json = load_json(
        event["combined_json_paths"]["1"]["bucket"],
        event["combined_json_paths"]["1"]["key"]
    )
    logging.info(f"Number of products in combined scraped data JSON: {len(combined_json)}")


    # Try to load and update JSON of master products table
    BUCKET = os.environ['BUCKET']
    master_prod_key = "master_data/all_product_ids_names.json"
    missed_prod_ids = []
    try:
        master_prods_dict = load_json(BUCKET, master_prod_key)
        logging.info(f"Number of products in master products table: {len(master_prods_dict)}")

        # Find out how many products we missed during scraping
        missed_prod_ids = list(set(master_prods_dict.keys()).difference(combined_json.keys()))
        logging.info(f"Number of products missing in scraped data: {len(missed_prod_ids)}")

        # Update master products table with new products from latest data
        master_prods_dict.update(combined_json)
        logging.info(f"Number of products in updated master products table: {len(master_prods_dict)}")

        # Save updated master products table
        s3object = s3.Object(
            BUCKET, master_prod_key
        )
        s3object.put(
            Body=(bytes(json.dumps(master_prods_dict).encode('UTF-8')))
        )
        logging.info(f"Saved updated master products table to S3")

    # Except create one if it doesn't exist and save to S3
    except botocore.exceptions.ClientError as ex:
        master_prods_dict = {prod_id: combined_json[prod_id]['name'] for prod_id in combined_json.keys()}
        logging.info(f"Master products table does not exist, creating one using scraped data...")

        # Save updated master products table
        s3object = s3.Object(
            BUCKET, master_prod_key
        )
        s3object.put(
            Body=(bytes(json.dumps(master_prods_dict).encode('UTF-8')))
        )
        logging.info(f"Saved new master products table to S3")

    # Partition the list of missed products
    if len(missed_prod_ids) > 0:

        # Check that the number of missed products isn't ridiculous
        assert(len(missed_prod_ids) <= int(0.333 * len(master_prods_dict))), "Too many products have been missed during scraping, something has gone wrong"

        # Partition missed products into partitions
        num_secs_per_page = 13  # Assume it takes x seconds to scrape a product page
        number_scrapers = math.ceil(((num_secs_per_page * len(missed_prod_ids)) / 60) / 12.5)
        num_items_in_partition = math.ceil(len(missed_prod_ids) / number_scrapers)
        logging.info(f"Number of scrapers needed to finish all missed products in 12.5 mins: {number_scrapers}")
        logging.info(f"Number of products to scrape for each scraper: {num_items_in_partition}")

        partitions = [
            {f'partition': missed_prod_ids[idx: idx + num_items_in_partition]}
            for i, idx in enumerate(range(0, len(missed_prod_ids), num_items_in_partition))
        ]

    else:
        partitions = []


    return partitions
