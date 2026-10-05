import os
import requests
from dotenv import load_dotenv

load_dotenv()


class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")

    def get_quote(self, symbol: str):
        response = requests.get(
            f"{self.BASE_URL}/quote",
            params={
                "symbol": symbol,
                "apikey": self.api_key
            }
        )

        response.raise_for_status()

        return response.json()