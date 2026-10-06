import os

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

from app.integrations.external_database.client import FMPClient

load_dotenv()


def salvar_cotacao_no_mongo(simbolo: str):
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI must be set in the environment or .env file")

    client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())
    try:
        colecao = client["integracao_db"]["respostas_api"]
        dados_cotacao = FMPClient().get_quote(symbol=simbolo)

        if dados_cotacao:
            if isinstance(dados_cotacao, list):
                resultado = colecao.insert_many(
                    [dict(documento) for documento in dados_cotacao]
                )
                print(
                    f"Cotação de '{simbolo}' salva com sucesso! "
                    f"Documentos inseridos: {len(resultado.inserted_ids)}"
                )
            else:
                resultado = colecao.insert_one(dict(dados_cotacao))
                print(
                    f"Cotação de '{simbolo}' salva com sucesso! "
                    f"ID: {resultado.inserted_id}"
                )
        else:
            print(f"Nenhum dado retornado para o símbolo: {simbolo}")
        return dados_cotacao
    finally:
        client.close()


if __name__ == "__main__":
    salvar_cotacao_no_mongo("AAPL")