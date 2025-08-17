"""Utility functions for the pipeline."""

import re

def is_valid_input(text: str) -> bool:
    """
    Validates if the input text is a valid string for processing.

    A valid string must not be None, must not be empty or whitespace-only,
    and must contain at least one alphabetical character (supports Unicode).

    Args:
        text: The input string to validate.

    Returns:
        True if the text is valid, False otherwise.
    """
    if not text or not text.strip():
        return False
    # Check if there is at least one letter character in the string.
    return any(c.isalpha() for c in text)
