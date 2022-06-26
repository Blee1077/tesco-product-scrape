import os
import boto3
import logging
import pandas as pd
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    # Specify the dtypes of columns to cast
    convert_dict = {
        'id': str,
        'name': str,
        'price_per_unit': float,
        'price_per_weight_quant': float,
        'weight_quant_unit': str,
        'offer': str,
        'category_1': str,
        'category_2': str,
        'category_3': str,
        'category_4': str,
    }

    # Load in scraped data from current run
    scraped_df = pd.read_csv(event)
    logging.info(f"Number of rows in scraped data from current run: {len(scraped_df)}")

    # Cast columns types
    for col, dtype in convert_dict.items():
        scraped_df[col] = scraped_df[col].astype(dtype)

    # Try loading in master scraped data table
    BUCKET = os.environ['BUCKET_NAME']
    master_data_path = "s3://{BUCKET}/master_data/scraped_product_data.parquet"
    try:
        master_df = pd.read_parquet(master_data_path)
        logging.info(f"Number of rows in master scraped data table: {len(master_df)}")

        # Concatenate the two dataframes and save
        master_df = pd.concat([master_df, scraped_df])
        master_df.to_parquet(master_data_path)
        logging.info(f"Number of rows in master scraped data table after concatenation: {len(master_df)}")

    # Otherwise if it doesn't exist then save current scaped data as master data
    except FileNotFoundError as ex:
        scraped_df.to_parquet(master_data_path)
        logging.info("Could not find master scraped data table, saved current table as master")

    return 200