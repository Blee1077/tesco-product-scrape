import json
import boto3
import datetime
import logging
from utilities import load_json
logging.getLogger().setLevel(logging.INFO)

s3 = boto3.resource('s3')

def lambda_handler(event, context):

    # Log the input
    logging.info(f"Input: {event}")

    # Get S3 bucket and keys of partition result JSONs
    if len(event['partition_results']) > 0:
        partition_result_bucket = event['partition_results'][0]['body']['bucket']
        partition_result_keys = [
            event['partition_results'][idx]['body']['key'] for idx in range(len(event['partition_results']))
        ]
    
        # Load them in and combine into a single dict
        combined_json = dict()
        for key in partition_result_keys:
            partition_result_json = load_json(
                bucket=partition_result_bucket, key=key
            )
            combined_json.update(partition_result_json)
        logging.info(f"Number of items in combined JSON: {len(combined_json)}")
    
        # Save combined JSON to S3
        curr_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_key = f'intermediate_data/{curr_datetime}_combined_data.json'
        s3object = s3.Object(
            partition_result_bucket, save_key
        )
        s3object.put(
            Body=(bytes(json.dumps(combined_json).encode('UTF-8')))
        )
        logging.info(f"Saved combined JSON to S3 at {save_key}")
        
    # If empty then return None
    else:
        partition_result_bucket = None
        save_key = None

    return {
        "bucket": partition_result_bucket,
        "key": save_key
    }
