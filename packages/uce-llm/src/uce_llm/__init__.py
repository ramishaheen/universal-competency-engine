"""Universal Competency Engine — LLM provider adapters."""
from uce_llm.base import (
    LLMError,
    LLMProvider,
    Message,
    Role,
    StreamChunk,
    TokenUsage,
    Response,
)
from uce_llm.registry import build_provider, get_provider_class, register_provider

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "LLMError",
    "LLMProvider",
    "Message",
    "Response",
    "Role",
    "StreamChunk",
    "TokenUsage",
    "build_provider",
    "get_provider_class",
    "register_provider",
]
