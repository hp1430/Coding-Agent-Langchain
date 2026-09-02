import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


@dataclass
class Provider:
    name: str
    env_var: str
    is_free: bool
    base_url: str | None
    model: str

PROVIDERS = [
    Provider(
        name="Groq",
        is_free=True,
        env_var="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        model="openai/gpt-oss-20b"
    )
]

def select_provider() -> Provider:
    for provider in PROVIDERS:
        if os.getenv(provider.env_var):
            return provider
    raise ValueError("No valid provider found. Please set the appropriate environment variable.")

def build_client_model() -> tuple[ChatOpenAI, Provider]:
    provider = select_provider()
    kwargs: dict = {
        "model": provider.model,
        "api_key": os.getenv(provider.env_var),
    }
    if provider.base_url:
        kwargs["base_url"] = provider.base_url
    return ChatOpenAI(**kwargs), provider
