"""Handles the generation of run metadata."""
    
import datetime
import logging
import os
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)

def _get_pipeline_version() -> str:
    """
    Retrieves the pipeline version from environment variable.
    
    This approach is more robust than git commands in Docker containers.
    The version should be set during Docker build via --build-arg.

    Returns:
        The pipeline version as a string, or "unknown" if not set.
    """
    return os.getenv("PIPELINE_VERSION", "unknown")


def generate_metadata(
    input_file: str,
    num_inputs: int,
    num_chunks: int,
    model_version: str = "model_v1",  # As per spec, can be made dynamic if needed
) -> Dict[str, Any]:
    """
    Generates a dictionary of metadata for the pipeline run.

    Args:
        input_file: The name of the input data file.
        num_inputs: The total number of lines processed from the input file.
        num_chunks: The total number of chunks generated.
        model_version: The version of the model used.

    Returns:
        A dictionary containing the run's metadata.
    """

    pipeline_version = _get_pipeline_version()
    metadata = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input_file": input_file,
        "num_inputs": num_inputs,
        "num_chunks": num_chunks,
        "model_version": model_version,
        "pipeline_version": pipeline_version,
    }

    logging.info(f"Generated metadata: {metadata}")
    return metadata
