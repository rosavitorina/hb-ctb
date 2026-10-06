import os

import requests
from dotenv import load_dotenv

load_dotenv()


class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise RuntimeError("FMP_API_KEY must be set in the environment or .env file")

    def get_quote(self, symbol: str):
        response = requests.get(
            f"{self.BASE_URL}/quote",
            params={"symbol": symbol, "apikey": self.api_key},
        )

        if not response.ok:
            message = f"FMP request failed with HTTP {response.status_code}"
            if response.status_code == 401:
                message += "; verify that FMP_API_KEY is valid and has access to this endpoint"
            raise RuntimeError(message)

        return response.json()