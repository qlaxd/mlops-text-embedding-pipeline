"""Handles communication with AWS S3 for storing pipeline outputs."""

import json

import logging

import time

from typing import Dict, Any



import boto3

from botocore.exceptions import ClientError



class S3Storage:

    """A class to manage uploading data to an S3 bucket."""



    def __init__(self, bucket_name: str, region_name: str = 'us-east-1'):

        """

        Initializes the S3Storage client.



        Args:

            bucket_name: The name of the S3 bucket.

            region_name: The AWS region of the bucket.

        """

        self.bucket_name = bucket_name

        self.s3_client = boto3.client('s3', region_name=region_name)



    def upload_json(

        self, 

        data: Dict[str, Any], 

        s3_key: str, 

        retries: int = 3, 

        delay: int = 5

    ) -> bool:

        """

        Uploads a dictionary as a JSON file to S3 with a retry mechanism.



        Args:

            data: The dictionary to upload.

            s3_key: The destination key (path) in the S3 bucket.

            retries: The number of times to retry on failure.

            delay: The delay in seconds between retries.



        Returns:

            True if upload was successful, False otherwise.

        """

        try:

            json_string = json.dumps(data, indent=2)

        except TypeError as e:

            logging.error(f"Failed to serialize data to JSON for S3 key {s3_key}: {e}")

            return False



        for attempt in range(retries):

            try:

                self.s3_client.put_object(

                    Bucket=self.bucket_name,

                    Key=s3_key,

                    Body=json_string,

                    ContentType='application/json'

                )

                logging.info(f"Successfully uploaded to s3://{self.bucket_name}/{s3_key}")

                return True

            except ClientError as e:

                # Retry only on potentially transient errors

                if e.response['Error']['Code'] in ['InternalError', 'ServiceUnavailable']:

                    logging.warning(

                        f"S3 upload failed on attempt {attempt + 1}/{retries} with error: {e}. Retrying in {delay}s..."

                    )

                    time.sleep(delay)

                else:

                    logging.error(f"An unrecoverable S3 ClientError occurred: {e}")

                    return False # Do not retry on non-transient errors

            except Exception as e:

                logging.error(f"An unexpected error occurred during S3 upload: {e}")

                return False

        

        logging.error(f"S3 upload failed after {retries} attempts.")

        return False

