
from typing import Any

from pymongo import MongoClient
from pymongo.results import InsertOneResult
from config.config import get_configs


class MongoDB:
    def __init__(self, database_name: str, url: str = None) -> None:
        
        if url is not None:
            self.client = MongoClient(url)
            self.database = self.client[database_name]
        else:
            app_configs = get_configs()
            self.client = MongoClient(app_configs.mongo_url)
            self.database = self.client[database_name]

    def create_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> None:
        if collection_name in self.database.list_collection_names():
            return

        self.database.create_collection(collection_name, **kwargs)

    def insert_document(
        self,
        collection_name: str,
        document: dict[str, Any],
    ) -> InsertOneResult:
        collection = self.database[collection_name]
        return collection.insert_one(document)

    def get_document(
        self,
        collection_name: str,
        filters: dict[str, Any],
    ) -> dict[str, Any] | None:
        collection = self.database[collection_name]
        return collection.find_one(filters)


if __name__ == "__main__":
    from pprint import pprint
    import base64
    import subprocess
    
    def get_mongo_password() -> str:
        secret_base64 = subprocess.check_output(
        [
            "kubectl",
            "get",
            "secret",
            "my-lib-bot-mongodb",
            "-o",
            "jsonpath={.data.mongodb-root-password}",
        ],
        text=True,
        )

        password = base64.b64decode(secret_base64).decode("utf-8")
        return password
    
    
    
    mongo_password = get_mongo_password()
    mongo = MongoDB(database_name="test", url=f"mongodb://root:{mongo_password}@localhost:27017")
    mongo.create_collection("test_collection")
    insert_response = mongo.insert_document(collection_name="test_collection", document={"id":0, "description": "this is only a test"})
    pprint(insert_response)
    doc = mongo.get_document(collection_name="test_collection", filters={"id": 0})
    pprint(doc)
    