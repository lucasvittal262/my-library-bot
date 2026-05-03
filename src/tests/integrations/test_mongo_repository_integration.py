import base64
import os
import subprocess
from uuid import uuid4

import pytest
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from repositories.mongo import MongoDB


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

    return base64.b64decode(secret_base64).decode("utf-8")


@pytest.fixture
def mongo_url() -> str:
    configured_url = os.getenv("MONGO_TEST_URL")
    if configured_url:
        return configured_url

    try:
        mongo_password = get_mongo_password()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest.skip(f"MongoDB Kubernetes secret is not available: {exc}")

    return f"mongodb://root:{mongo_password}@localhost:27017/?authSource=admin"


@pytest.mark.integration
def test_mongodb_insert_and_get_document(mongo_url: str) -> None:
    database_name = f"test_{uuid4().hex[:8]}"
    collection_name = f"test_collection_{uuid4().hex[:8]}"
    document = {"id": 0, "description": "this is only a test"}

    mongo = MongoDB(database_name=database_name, url=mongo_url)

    try:
        mongo.client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        pytest.skip(f"MongoDB is not available at localhost:27017: {exc}")

    try:
        mongo.create_collection(collection_name)
        insert_response = mongo.insert_document(
            collection_name=collection_name,
            document=document,
        )
        found_document = mongo.get_document(
            collection_name=collection_name,
            filters={"id": 0},
        )

        assert insert_response.acknowledged is True
        assert found_document is not None
        assert found_document["id"] == document["id"]
        assert found_document["description"] == document["description"]
        assert "_id" in found_document
    except PyMongoError as exc:
        pytest.fail(f"MongoDB integration operation failed: {exc}")
    finally:
        mongo.client.drop_database(database_name)
