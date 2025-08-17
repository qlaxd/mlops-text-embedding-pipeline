"""Orchestrates the main text embedding pipeline workflow."""

import datetime
import logging
import os
from src import config, embedder, metadata, storage, utils


def run():
    """
    Executes the full MLOps text embedding pipeline.
    - Loads configuration.
    - Initializes services (Embedder, S3Storage).
    - Reads and processes input data line by line.
    - Validates, chunks, and creates embeddings.
    - Aggregates results and uploads them to S3.
    - Generates and uploads run metadata to S3.
    """

    logging.info("Starting MLOps Text Embedding Pipeline run...")

    try:
        # 1. Initialization
        app_config = config.load_config()
        s3_bucket = app_config["s3_bucket_name"]
        aws_region = app_config.get("aws_region")
        input_file_path = app_config["input_data_path"]
        embedding_service = embedder.Embedder(
            model_path=app_config["model_path"],
            max_seq_length=app_config["max_seq_length"],
        )
        storage_service = storage.S3Storage(bucket_name=s3_bucket, region_name=aws_region)
        all_chunks = []
        processed_lines = 0

        # 2. Data Processing
        logging.info(f"Reading input data from: {input_file_path}")

        with open(input_file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line_text = line.strip()
                if not utils.is_valid_input(line_text):
                    logging.warning(
                        f'Skipping invalid input on line {i+1}: "{line_text[:100]}..."'
                    )
                    continue

                processed_lines += 1
                chunks = embedding_service.process_text(line_text)

                if chunks:
                    all_chunks.extend(chunks)

        if not all_chunks:
            logging.warning("No valid text was processed. No output will be generated.")
            return

        # 3. Aggregation and Storage
        output_data = {"embeddings": {"chunks": all_chunks}}
        run_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        output_s3_key = f"embeddings/{run_timestamp}.json"
        storage_service.upload_json(data=output_data, s3_key=output_s3_key)

        # 4. Metadata Logging
        run_metadata = metadata.generate_metadata(
            input_file=os.path.basename(input_file_path),
            num_inputs=processed_lines,
            num_chunks=len(all_chunks),
        )
        metadata_s3_key = f"metadata/{run_timestamp}.json"
        storage_service.upload_json(data=run_metadata, s3_key=metadata_s3_key)
        logging.info("Pipeline run finished successfully.")

    except (FileNotFoundError, ValueError, Exception) as e:
        logging.critical(
            f"A critical error occurred during the pipeline run: {e}", exc_info=True
        )
        # In a real-world scenario, this could trigger an alert.
        raise
