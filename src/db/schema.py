from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

from embedding import GraniteEmbedder


model = get_registry().get("granite-embedder").create()


class TourChunk(LanceModel):
    tournr: str
    chunk_id: str
    text: str = model.SourceField()
    vector: Vector(model.ndims()) = model.VectorField()


class Chunk(LanceModel):
    chunk_id: str
    filename: str
    text: str = model.SourceField()
    vector: Vector(model.ndims()) = model.VectorField()
