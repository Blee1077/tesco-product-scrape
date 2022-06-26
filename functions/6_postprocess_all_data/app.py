import os
import boto3
import datetime
import logging
import pandas as pd
from utilities import load_json
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def convert_dict_to_dataframe(prod_dict):
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

    # Convert the dict into a dataframe
    prod_df = pd.DataFrame.from_records(prod_dict).T.reset_index()
    prod_df = prod_df.rename(columns={'index': 'id'})

    # Cast columns
    for col, dtype in convert_dict.items():
        prod_df[col] = prod_df[col].astype(dtype)

    return prod_df


def convert_curr_to_float(curr: str):
    if isinstance(curr, str):
        if '£' in curr:
            return float(curr.replace('£', ''))
        elif 'p' in curr:
            return float(curr.replace('p', '')) / 100
        else:
            return None
    else:
        return None


def lambda_handler(event, context):
    # Load in combined JSONs and add to a master dict
    all_data_json = {}
    for path_idx in event["combined_json_paths"].keys():
        if event["combined_json_paths"][path_idx]["key"] is None:
            continue
        else:
            combined_json = load_json(
                event["combined_json_paths"][path_idx]["bucket"],
                event["combined_json_paths"][path_idx]["key"]
            )
            all_data_json.update(combined_json)
    logging.info(f"Total of products scraped: {len(all_data_json)}")

    # Convert dict into dataframe
    prod_df = convert_dict_to_dataframe(all_data_json)
    logging.info(f"Number of items in converted dataframe: {len(prod_df)}")

    # Calculate clubcard discount percentage
    prod_df['clubcard_price_per_unit'] = prod_df['offer'].apply(lambda x: x.split(' ')[0] if len(x.split(' '))==3 else None)
    prod_df['clubcard_price_per_unit'] = prod_df['clubcard_price_per_unit'].apply(lambda x: convert_curr_to_float(x))
    prod_df['clubcard_discount_perc'] =  100 * (1 - (prod_df['clubcard_price_per_unit'] / prod_df['price_per_unit']))
    
    # Add date column
    prod_df['date'] = pd.Timestamp.today().date()
    
    # Save processed dataframe to S3
    BUCKET = os.environ['BUCKET_NAME']
    curr_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_path = f's3://{BUCKET}/processed_data/{curr_datetime}_processed_data.csv'
    prod_df.to_csv(save_path, index=False)
    logging.info(f"Saved dataframe to S3 at {save_path}")

    return save_path