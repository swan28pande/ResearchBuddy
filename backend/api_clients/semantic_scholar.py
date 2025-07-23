import os
import requests

class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})

    def search(self, query, limit=5, fields=None):
        """
        Search for papers by keyword/topic.
        :param query: Search query string
        :param limit: Number of results to return
        :param fields: List of fields to return (default: title,authors,year,abstract,url,citationCount)
        :return: List of paper dicts
        """
        if fields is None:
            fields = ["title", "authors", "year", "abstract", "url", "citationCount"]
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": ",".join(fields)
        }
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"Semantic Scholar search error: {response.status_code} {response.text}")
            return []

    def get_paper(self, paper_id, fields=None):
        """
        Retrieve detailed information about a specific paper.
        :param paper_id: Semantic Scholar paper ID
        :param fields: List of fields to return (default: title,authors,year,abstract,url,citationCount)
        :return: Paper dict or None
        """
        if fields is None:
            fields = ["title", "authors", "year", "abstract", "url", "citationCount"]
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": ",".join(fields)}
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Semantic Scholar get_paper error: {response.status_code} {response.text}")
            return None
