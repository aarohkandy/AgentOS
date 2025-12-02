"""
llama.cpp backend implementation.

This provides a concrete LLM backend using llama.cpp via llama-cpp-python bindings.
"""

from __future__ import annotations

from typing import List, Optional

from .llm_interface import LLMBackend
from .types import Message


try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


class LlamaCppBackend(LLMBackend):
    """
    llama.cpp-based backend for local LLM inference.

    Uses llama-cpp-python bindings to run quantized models locally.
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_threads: int = 4,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        stop_sequences: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize llama.cpp backend.

        Args:
            model_path: Path to the quantized model file (.gguf)
            n_ctx: Context window size
            n_threads: Number of threads for inference
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling
            stop_sequences: List of stop sequences for generation
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.stop_sequences = stop_sequences or []
        self._model = None  # Lazy-loaded

    def _load_model(self) -> None:
        """Load the model (lazy initialization)."""
        if self._model is not None:
            return

        if Llama is None:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Run: ./scripts/setup-llama-cpp.sh"
            )

        self._model = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            verbose=False,
        )

    def _format_messages(self, messages: List[Message]) -> str:
        """
        Format messages into a prompt string.

        Uses ChatML format which works well with most instruct models.
        """
        formatted = ""
        for msg in messages:
            if msg.role == "system":
                formatted += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
            elif msg.role == "user":
                formatted += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
            elif msg.role == "assistant":
                formatted += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"

        # Add assistant prefix for the response
        formatted += "<|im_start|>assistant\n"
        return formatted

    def generate(self, messages: List[Message], max_tokens: int = 256) -> Message:
        """
        Generate response using llama.cpp.

        Args:
            messages: Conversation history
            max_tokens: Maximum tokens to generate

        Returns:
            Message with assistant role containing the generated response
        """
        if self._model is None:
            self._load_model()

        prompt = self._format_messages(messages)

        # Generate response
        result = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop=self.stop_sequences,
            echo=False,
        )

        # Extract generated text
        generated_text = result["choices"][0]["text"].strip()

        return Message(role="assistant", content=generated_text)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the model's tokenizer.

        Args:
            text: Text to tokenize

        Returns:
            Number of tokens
        """
        if self._model is None:
            self._load_model()

        tokens = self._model.tokenize(text.encode("utf-8"))
        return len(tokens)


