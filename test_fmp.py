from app.integrations.external_database.client import FMPClient


client = FMPClient()

result = client.get_quote("NVDA")

print(result)