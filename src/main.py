"""Main entry point for the MLOps Text Embedding Pipeline."""

import logging
import sys
from src import pipeline

def main():
    """
    Sets up logging and runs the main pipeline.
    """

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        stream=sys.stdout, # Log to stdout, which is captured by Docker/CloudWatch
    )

    try:
        pipeline.run()

    except Exception as e:
        logging.fatal(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

