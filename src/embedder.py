"""Handles model loading, text chunking, and embedding generation."""

import logging
import textwrap
from typing import Any, Dict, List, Optional
import joblib

class Embedder:
    """A wrapper for the embedding model to handle loading and processing."""

    def __init__(self, model_path: str, max_seq_length: int):
        """
        Initializes the Embedder and loads the model.
        Args:
            model_path: Path to the model.joblib file.
            max_seq_length: The maximum sequence length the model can handle.
        """

        self.model: Any = self._load_model(model_path)
        self.max_seq_length = max_seq_length

    def _load_model(self, model_path: str) -> Any:
        """Loads the model from the specified path."""

        try:
            logging.info(f"Loading model from {model_path}...")
            model = joblib.load(model_path)
            logging.info("Model loaded successfully.")
            return model

        except FileNotFoundError:
            logging.error(f"Model file not found at: {model_path}")
            raise

        except Exception as e:
            logging.error(f"An unexpected error occurred while loading the model: {e}")
            raise



    def _chunk_text(self, text: str) -> List[str]:
        """Splits text into chunks that fit the model's max sequence length."""
        if len(text) <= self.max_seq_length:
            return [text]
        
        logging.debug(f"Text length ({len(text)}) exceeds max sequence length. Chunking...")
        return textwrap.wrap(text, self.max_seq_length, break_long_words=True, replace_whitespace=False)



    def process_text(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Chunks the text and generates embeddings for each chunk.
        Args:
            text: The input text to process.

        Returns:
            A list of dictionaries, where each dictionary contains a text chunk
            and its corresponding embedding vector. Returns None if input is invalid.
        """

        chunks = self._chunk_text(text)
        if not chunks:
            return None

        try:
            logging.debug(f"Generating embeddings for {len(chunks)} chunks.")
            embeddings = self.model.encode(chunks)

            # Ensure embeddings are JSON-serializable (list of lists of floats)
            serializable_embeddings = [embedding.tolist() for embedding in embeddings]

            return [{"text": chunk, "vector": vec} for chunk, vec in zip(chunks, serializable_embeddings)]

        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            return None

