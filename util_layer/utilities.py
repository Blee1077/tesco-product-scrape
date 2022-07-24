"""Contains utility functions that are commonly used between lambda functions."""
import json
import pickle
import boto3
s3 = boto3.resource('s3')

def load_pickle(bucket: str, key: str) -> dict:
    """Loads a pickle file from S3 bucket.

    Args:
        bucket (str): S3 bucket containing pickle file
        key (str): Path within bucket of pickle file

    Returns:
        list or dict
    """
    content_object = s3.Object(bucket, key)
    file_content = content_object.get()["Body"].read()
    return pickle.loads(file_content)


def load_json(bucket: str, key: str) -> dict:
    """Loads a JSON file from S3 bucket.

    Args:
        bucket (str): S3 bucket containing JSON file
        key (str): Path within bucket of JSON file

    Returns:
        dict
    """
    content_object = s3.Object(bucket, key)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    return json.loads(file_content)


def load_proxy_details(bucket: str, key: str) -> tuple:
    """Loads in proxy details to bypass companies blocking public AWS IP addresses.

    Args:
        bucket (str): S3 bucket containing JSON file
        key (str): Path within bucket of JSON file

    Returns:
        proxy_dict (dict): Proxy details to use with GET requests
        proxy_details["expiry"] (str): Date of expiry
    """
    # Load JSON containing proxy details from S3
    proxy_details = load_json(bucket=bucket, key=key)

    # Construct http connection address
    http_connection = "socks5://{}:{}@{}:{}".format(
        proxy_details["username"],
        proxy_details["password"],
        proxy_details["address"],
        proxy_details["port"]
    )

    # Store in dictionary
    proxy_dict = {
        'https': http_connection,
        'http': http_connection
    }

    return proxy_dict, proxy_details["expiry"]