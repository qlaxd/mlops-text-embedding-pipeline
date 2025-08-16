"""Handles loading configuration from YAML and environment variables."""

import logging

import os

from typing import Any, Dict



import yaml



CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')



def load_config() -> Dict[str, Any]:

    """

    Loads configuration from the YAML file and overrides with environment variables.



    Uses yaml.safe_load for security. The S3 bucket name can be overridden

    by the S3_BUCKET_NAME environment variable.



    Returns:

        A dictionary containing the configuration.



    Raises:

        FileNotFoundError: If the config.yaml file is not found.

        ValueError: If the S3 bucket name is not configured.

    """

    try:

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:

            config = yaml.safe_load(f)

    except FileNotFoundError:

        logging.error(f"Configuration file not found at: {CONFIG_PATH}")

        raise



    pipeline_config = config.get('pipeline', {})



    # Override S3 bucket name with environment variable if available

    s3_bucket_env = os.getenv('S3_BUCKET_NAME')

    if s3_bucket_env:

        pipeline_config['s3_bucket_name'] = s3_bucket_env

        logging.info(f"Loaded S3 bucket name from environment variable: {s3_bucket_env}")



    if not pipeline_config.get('s3_bucket_name') or pipeline_config['s3_bucket_name'] == 'your-bucket-name-placeholder':

        raise ValueError("S3 bucket name is not configured. Please set it in config.yaml or via S3_BUCKET_NAME env var.")



    return pipeline_config

