import os
import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.infrastructure.database.mongo import listar_cotacoes_no_mongo


class ListSavedQuotesTests(unittest.TestCase):
    def test_lists_newest_quotes_with_string_ids_and_limit(self):
        documents = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "symbol": "AAPL"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "symbol": "NVDA"},
        ]
        mongo_client = MagicMock()
        collection = mongo_client["integracao_db"]["respostas_api"]
        cursor = collection.find.return_value.sort.return_value
        cursor.limit.return_value = documents

        with patch.dict(os.environ, {"MONGO_URI": "mongodb://test"}, clear=True):
            with patch(
                "app.infrastructure.database.mongo.MongoClient",
                return_value=mongo_client,
            ) as client_constructor:
                quotes = listar_cotacoes_no_mongo(limite=2)

        collection.find.assert_called_once_with()
        collection.find.return_value.sort.assert_called_once_with("timestamp", -1)
        cursor.limit.assert_called_once_with(2)
        client_constructor.assert_called_once()
        mongo_client.close.assert_called_once_with()
        self.assertEqual([quote["symbol"] for quote in quotes], ["AAPL", "NVDA"])
        self.assertEqual(quotes[0]["_id"], "507f1f77bcf86cd799439011")

    def test_requires_mongo_uri(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.infrastructure.database.mongo.MongoClient") as client_constructor:
                with self.assertRaisesRegex(RuntimeError, "MONGO_URI"):
                    listar_cotacoes_no_mongo()

        client_constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()