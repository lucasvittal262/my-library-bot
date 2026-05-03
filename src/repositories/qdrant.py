from pprint import pprint
from fastembed import SparseEmbedding
from qdrant_client import QdrantClient, models
from config.config import get_configs
from typing import List


class QdrantVectorDB:
    def __init__(self, collection_name: str, url: str = None):

        self.collection_name = collection_name
        if url is not None:
            self.client = QdrantClient(url=url)

        else:
            app_configs = get_configs()
            self.client = QdrantClient(url=app_configs.qdrant_url)

    def get_docs_by_hibrid_search(
        self,
        dense_vector_input: List[float],
        sparse_vector_input: SparseEmbedding,
        top_k: int,
    ) -> models.QueryResponse:
        prefetch = [
            models.Prefetch(
                query=dense_vector_input,
                using="dense",
                limit=top_k * 2,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector_input.indices.tolist(),
                    values=sparse_vector_input.values.tolist(),
                ),
                using="sparse",
                limit=top_k * 2,
            ),
        ]

        results = self.client.query_points(
            self.collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            with_payload=True,
            limit=top_k,
        )
        return results


if __name__ == "__main__":
    from services.embedding import OpenAIEmbeddingService
    from fastembed import SparseTextEmbedding

    def create_collection(
        client: QdrantClient, collection_name: str, dim_dense_vector: int
    ) -> None:
        if client.collection_exists(collection_name=collection_name):
            client.delete_collection(collection_name=collection_name)

        client.create_collection(
            collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=dim_dense_vector,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )

    COLLECTION_NAME = "test3"
    CITIES_DESCRIPTIONS = {
        "London": "A global financial and cultural capital, known for its history, iconic landmarks like Big Ben and the Thames, and its influence in finance, fashion, and the arts.",
        "Moscow": "Russia’s capital and political center, famous for the Kremlin, Red Square, and its rich history blending imperial and Soviet eras.",
        "New York": "A fast-paced global hub for finance, media, and culture, home to Wall Street, Broadway, and landmarks like the Statue of Liberty.",
        "Beijing": "China’s capital, combining ancient heritage (like the Forbidden City) with modern political and economic significance.",
        "Mumbai": "India’s financial powerhouse and entertainment capital, known for Bollywood, dense urban life, and coastal energy.",
    }

    bm25_model = SparseTextEmbedding(model_name="qdrant/bm25")
    embedding_service = OpenAIEmbeddingService(embedding_model="text-embedding-3-small")
    client_test = QdrantClient(url="localhost:6333")
    create_collection(
        client=client_test, collection_name=COLLECTION_NAME, dim_dense_vector=1536
    )

    description_embeddings = [
        {
            "dense_vector": embedding_service.get_embedding(description).embedding,
            "sparse_vector": next(bm25_model.embed(description)),
            "city": city,
        }
        for city, description in CITIES_DESCRIPTIONS.items()
    ]

    operation_info = client_test.upsert(
        collection_name=COLLECTION_NAME,
        wait=True,
        points=[
            models.PointStruct(
                id=idx,
                vector={
                    "dense": row["dense_vector"],
                    "sparse": models.SparseVector(
                        indices=row["sparse_vector"].indices.tolist(),
                        values=row["sparse_vector"].values.tolist(),
                    ),
                },
                payload={"city": row["city"]},
            )
            for idx, row in enumerate(description_embeddings)
        ],
    )

    vector_db = QdrantVectorDB(collection_name=COLLECTION_NAME, url="localhost:6333")
    query_txt = "A city with is the  global center of for finance, media, and culture"
    sparse_vector = next(bm25_model.embed(query_txt))
    query_vector = embedding_service.get_embedding(query_txt).embedding
    results = vector_db.get_docs_by_hibrid_search(
        dense_vector_input=query_vector, sparse_vector_input=sparse_vector, top_k=3
    )
    pprint(results)
