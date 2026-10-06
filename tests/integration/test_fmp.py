from app.integrations.external_database.client import FMPClient


def main():
	client = FMPClient()
	result = client.get_quote("NVDA")
	print(result)


if __name__ == "__main__":
	main()

# Testar o FMP isoladamente para facilitar diagnosticos possiveis.