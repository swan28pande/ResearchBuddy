import requests
import json

class TavilyClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query):
        # Replace with actual Tavily API endpoint and parameters
        url = "https://api.tavily.com/search"
        headers = {'Content-Type': 'application/json',"Authorization": f"Bearer {self.api_key}"}
        params = json.dumps({"query": query, "max_results": 3})
        response = requests.request("POST", url, headers=headers, data=params)
        if response.status_code == 200:
            return response.json().get("results", [])
        return []