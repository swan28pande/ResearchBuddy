import requests

class ArxivClient:
    def search(self, query):
        url = "http://export.arxiv.org/api/query"
        params = {"search_query": query, "start": 0, "max_results": 3}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return [response.text]
        return []