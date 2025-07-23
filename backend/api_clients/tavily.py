import requests

class TavilyClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query):
        # Replace with actual Tavily API endpoint and parameters
        url = "https://api.tavily.com/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"query": query, "num_results": 3}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("results", [])
        return []