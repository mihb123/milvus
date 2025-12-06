import os
from pymilvus import MilvusClient
from extractor import FEATURE_DIMENSION

MILVUS_URI = os.path.expanduser("./milvus.db")
COLLECTION_NAME = "image_embeddings"

class MilvusManager:
    def __init__(self, uri=MILVUS_URI, dimension=FEATURE_DIMENSION, collection_name=COLLECTION_NAME):
        self.client = MilvusClient(uri=uri)
        self.collection_name = collection_name
        self._setup_collection(dimension)

    def _setup_collection(self, dimension):
        if self.client.has_collection(self.collection_name):
            return

        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=dimension,
                primary_field_name="id",
                vector_field_name="vector",
                id_type="int",
                auto_id=True,
                enable_dynamic_field=True,
                metric_type="COSINE",
            )
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise e

    def insert_batch(self, data: list):
        if not data:
            return
        return self.client.insert(self.collection_name, data)

    def search_images(self, query_vector: list, limit: int = 10):
        return self.client.search(
            self.collection_name,
            data=[query_vector],
            output_fields=["filename", "name_key"],
            search_params={"metric_type": "COSINE", "params": {}},
            limit=limit,
        )

    def has_data(self):
        try:
            res = self.client.query(
                self.collection_name,
                filter="id >= 0",
                output_fields=["id"],
                limit=1
            )
            return len(res) > 0
        except:
            return False
    
    def check_file_exists(self, filename: str):
        try:
            res = self.client.query(
                self.collection_name,
                filter=f'filename == "{filename}"',
                output_fields=["id"],
                limit=1
            )
            return len(res) > 0
        except Exception as e:
            print(f"Check exists error: {e}")
            return False