"""Utility functions for the pipeline."""

import re



# This regex pattern checks for the presence of at least one letter.

# It is used to filter out lines that contain only numbers, punctuation, emojis, etc.

_HAS_LETTER_PATTERN = re.compile(r'[a-zA-Z]')



def is_valid_input(text: str) -> bool:

    """

    Validates if the input text is a valid string for processing.



    A valid string must not be None, must not be empty or whitespace-only,

    and must contain at least one alphabetical character.



    Args:

        text: The input string to validate.



    Returns:

        True if the text is valid, False otherwise.

    """

    if not text or not text.strip():

        return False

    return _HAS_LETTER_PATTERN.search(text) is not None

