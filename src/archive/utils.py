import configparser
import os
from typing import Dict
from datetime import datetime as dt


def get_config(path: str = "../config.ini") -> Dict:
    config = configparser.ConfigParser()
    config.read(path)
    return config._sections


def get_credentials(path: str = "../.credentials") -> Dict:
    config = configparser.ConfigParser()
    config.read(path)
    return config._sections["credentials"]


def read_file_from_s3(path):
    import boto3

    bucket_name = "faysal"
    region = "us-west-2"

    S3 = boto3.client(
        "s3",
        region_name=region,
        # aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
        # aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
    )
    # Create a file object using the bucket and object key.
    fileobj = S3.get_object(Bucket=bucket_name, Key=path)
    # open the file object and read it into the variable filedata.
    fileData = fileobj["Body"].read()
    return fileData.decode("utf-8")


def read_csv_from_s3(
    bucket_name, region, remote_file_name, aws_access_key_id, aws_secret_access_key
):
    # reads a csv from AWS

    # first you stablish connection with your passwords and region id

    # next you obtain the key of the csv you want to read
    # you will need the bucket name and the csv file name

    # you store it into a string, therefore you will need to split it
    # usually the split characters are '\r\n' if not just read the file normally
    # and find out what they are

    reader = csv.reader(data.split("\r\n"))
    data = []
    header = next(reader)
    for row in reader:
        data.append(row)

    return data
