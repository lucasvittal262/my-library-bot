from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pymongo.results import InsertOneResult

import repositories.mongo as mongo_repository
from repositories.mongo import MongoDB


@pytest.fixture
def mongo_client_constructor_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    constructor = Mock()
    monkeypatch.setattr(mongo_repository, "MongoClient", constructor)
    return constructor


def test_mongodb_uses_url_from_config_when_url_is_not_provided(
    monkeypatch: pytest.MonkeyPatch,
    mongo_client_constructor_mock: Mock,
) -> None:
    database = Mock()
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    monkeypatch.setattr(
        mongo_repository,
        "get_configs",
        Mock(return_value=SimpleNamespace(mongo_url="mongodb://config-url:27017")),
    )

    mongodb = MongoDB(database_name="library")

    mongo_client_constructor_mock.assert_called_once_with("mongodb://config-url:27017")
    client.__getitem__.assert_called_once_with("library")
    assert mongodb.client is client
    assert mongodb.database is database


def test_mongodb_uses_explicit_url_when_provided(
    mongo_client_constructor_mock: Mock,
) -> None:
    database = Mock()
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client

    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    mongo_client_constructor_mock.assert_called_once_with("mongodb://localhost:27017")
    client.__getitem__.assert_called_once_with("library")
    assert mongodb.database is database


def test_create_collection_creates_collection_when_it_does_not_exist(
    mongo_client_constructor_mock: Mock,
) -> None:
    database = Mock()
    database.list_collection_names.return_value = ["users"]
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    result = mongodb.create_collection("books", validator={"$jsonSchema": {}})

    assert result is None
    database.create_collection.assert_called_once_with(
        "books",
        validator={"$jsonSchema": {}},
    )


def test_create_collection_does_not_recreate_existing_collection(
    mongo_client_constructor_mock: Mock,
) -> None:
    database = Mock()
    database.list_collection_names.return_value = ["books"]
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    result = mongodb.create_collection("books")

    assert result is None
    database.create_collection.assert_not_called()


def test_insert_document_writes_document_to_collection(
    mongo_client_constructor_mock: Mock,
) -> None:
    insert_result = InsertOneResult(inserted_id="doc-id", acknowledged=True)
    collection = Mock()
    collection.insert_one.return_value = insert_result
    database = Mock()
    database.__getitem__ = Mock(return_value=collection)
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    document = {"id": 1, "description": "unit test"}
    result = mongodb.insert_document("books", document)

    database.__getitem__.assert_called_once_with("books")
    collection.insert_one.assert_called_once_with(document)
    assert isinstance(result, InsertOneResult)
    assert result.inserted_id == "doc-id"
    assert result.acknowledged is True


def test_get_document_reads_single_document_from_collection(
    mongo_client_constructor_mock: Mock,
) -> None:
    expected_document = {"id": 1, "description": "unit test"}
    collection = Mock()
    collection.find_one.return_value = expected_document
    database = Mock()
    database.__getitem__ = Mock(return_value=collection)
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    filters = {"id": 1}
    result = mongodb.get_document("books", filters)

    database.__getitem__.assert_called_once_with("books")
    collection.find_one.assert_called_once_with(filters)
    assert result == expected_document


def test_get_document_returns_none_when_no_document_matches(
    mongo_client_constructor_mock: Mock,
) -> None:
    collection = Mock()
    collection.find_one.return_value = None
    database = Mock()
    database.__getitem__ = Mock(return_value=collection)
    client = Mock()
    client.__getitem__ = Mock(return_value=database)
    mongo_client_constructor_mock.return_value = client
    mongodb = MongoDB(database_name="library", url="mongodb://localhost:27017")

    result = mongodb.get_document("books", {"id": 999})

    assert result is None
