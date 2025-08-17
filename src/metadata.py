"""Handles the generation of run metadata."""
    
import datetime
import logging
import subprocess
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)

def _get_git_commit_hash() -> Optional[str]:
    """
    Retrieves the current Git commit hash.

    Returns:
        The Git commit hash as a string, or None if it cannot be retrieved.
    """

    try:
        # The --git-dir and --work-tree arguments are added to ensure this command
        # works even if the script is not run from the repository root.
        # This is not strictly necessary for Docker but is good practice.
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd="./",  # Ensure it runs in the correct directory context
        )
        return result.stdout.strip()

    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.warning(
            "Could not determine Git commit hash. Not a git repository or git is not installed."
        )
        return None


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

    pipeline_version = _get_git_commit_hash()
    metadata = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input_file": input_file,
        "num_inputs": num_inputs,
        "num_chunks": num_chunks,
        "model_version": model_version,
        "pipeline_version": pipeline_version or "unknown",
    }

    logging.info(f"Generated metadata: {metadata}")
    return metadata
