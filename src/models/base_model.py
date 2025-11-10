"""Base model management utilities."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from src.utils.logger import get_logger

logger = get_logger()

try:  # pragma: no cover - optional heavy dependency
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - handled gracefully in environments without deps
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore


@dataclass
class GenerationParams:
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9


class BaseModelManager:
    """Utility class to load and interact with the base language model."""

    def __init__(
        self,
        model_name: str,
        quantization_config: Optional[Dict[str, Any]] = None,
        generation_params: Optional[GenerationParams] = None,
    ) -> None:
        self.model_name = model_name
        self.quantization_config = quantization_config or {}
        self.generation_params = generation_params or GenerationParams()
        self._model = None
        self._tokenizer = None
        logger.debug("Initialized BaseModelManager for model: {}", model_name)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def load_model(self) -> None:
        """Lazily load the base model into memory."""
        if self.is_loaded:
            logger.debug("Model already loaded, skipping load step.")
            return
        if AutoModelForCausalLM is None or AutoTokenizer is None:
            raise RuntimeError(
                "transformers is not installed. Please install the required dependencies."
            )

        logger.info("Loading base model '{}'", self.model_name)
        kwargs = {"device_map": "auto"}
        kwargs.update(self.quantization_config)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name, **kwargs)
        logger.success("Base model '{}' loaded successfully", self.model_name)

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            logger.info("Unloading base model '{}'", self.model_name)
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

    @contextmanager
    def ensure_loaded(self) -> Iterable[None]:
        try:
            if not self.is_loaded:
                self.load_model()
            yield
        finally:
            # Keep the model loaded for reuse; unloading handled manually when needed.
            logger.debug("Leaving ensure_loaded context for '{}'.", self.model_name)

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> str:
        if not self.is_loaded:
            raise RuntimeError("Model must be loaded before calling generate().")

        params = GenerationParams(
            max_new_tokens=max_new_tokens or self.generation_params.max_new_tokens,
            temperature=temperature or self.generation_params.temperature,
            top_p=top_p or self.generation_params.top_p,
        )

        inputs = self._tokenizer(  # type: ignore[operator]
            prompt,
            return_tensors="pt",
        )
        logger.debug("Generating response with params: {}", params)
        output_ids = self._model.generate(  # type: ignore[operator]
            **inputs,
            max_new_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )
        return self._tokenizer.decode(output_ids[0], skip_special_tokens=True)  # type: ignore[operator]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "quantization": self.quantization_config,
            "generation": self.generation_params.__dict__,
        }
