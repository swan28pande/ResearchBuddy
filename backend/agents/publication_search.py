class PublicationSearchAgent:
    def __init__(self, pub_api_clients):
        self.pub_api_clients = pub_api_clients  # List of clients

    def search(self, query):
        results = []
        for client in self.pub_api_clients:
            results.extend(client.search(query))
        return results