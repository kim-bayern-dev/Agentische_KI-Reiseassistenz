import os
from typing import Any
from ollama import Client
from lancedb.embeddings import register, TextEmbeddingFunction


@register("granite-embedder")
class GraniteEmbedder(TextEmbeddingFunction):

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        model_name: str = os.getenv("OLLAMA_EMBED_MODEL")
        base_url: str = os.getenv("OLLAMA_BASE_URL")
        client: Any = Client(host=base_url, headers={})
        batch = client.embed(model=model_name, input=texts)
        return batch["embeddings"]

    def ndims(self) -> int:
        # Return the dimensionality of the embeddings
        return len(self.generate_embeddings(["test"])[0])
