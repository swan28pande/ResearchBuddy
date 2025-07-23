class InternetSearchAgent:
    def __init__(self, web_api_client):
        self.web_api_client = web_api_client

    def search(self, query):
        return self.web_api_client.search(query)