import requests
import xml.etree.ElementTree as ET

class ArxivClient:
    def __init__(self, max_results=10):
        """
        Initialize arXiv API client.
        
        Args:
            max_results: Maximum number of papers to retrieve (default: 10)
        """
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results = max_results
        self.namespace = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
    
    def search(self, query):
        """
        Search arXiv and return structured paper metadata.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing paper metadata:
            - title: Paper title
            - abstract: Paper abstract
            - authors: List of author names
            - published: Publication date
            - pdf_url: Direct link to PDF
            - arxiv_id: arXiv identifier
            - categories: Subject classifications
        """
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            papers = []
            
            # Extract each paper entry
            for entry in root.findall('atom:entry', self.namespace):
                paper = {
                    'title': self._get_text(entry, 'atom:title'),
                    'abstract': self._get_text(entry, 'atom:summary'),
                    'authors': self._get_authors(entry),
                    'published': self._get_text(entry, 'atom:published'),
                    'pdf_url': self._get_pdf_link(entry),
                    'arxiv_id': self._extract_arxiv_id(self._get_text(entry, 'atom:id')),
                    'categories': self._get_categories(entry)
                }
                papers.append(paper)
            
            print(f"✓ Retrieved {len(papers)} papers from arXiv")
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching from arXiv API: {e}")
            return []
        except ET.ParseError as e:
            print(f"✗ Error parsing arXiv XML response: {e}")
            return []
        except Exception as e:
            print(f"✗ Unexpected error in arXiv search: {e}")
            return []
    
    def _get_text(self, entry, tag):
        """Safely extract text from XML element"""
        elem = entry.find(tag, self.namespace)
        return elem.text.strip() if elem is not None and elem.text else ""
    
    def _get_authors(self, entry):
        """Extract all author names"""
        authors = []
        for author in entry.findall('atom:author', self.namespace):
            name = author.find('atom:name', self.namespace)
            if name is not None and name.text:
                authors.append(name.text.strip())
        return authors
    
    def _get_pdf_link(self, entry):
        """Extract PDF download link"""
        for link in entry.findall('atom:link', self.namespace):
            if link.get('title') == 'pdf':
                return link.get('href', '')
        return ""
    
    def _get_categories(self, entry):
        """Extract subject categories"""
        categories = []
        for cat in entry.findall('atom:category', self.namespace):
            term = cat.get('term')
            if term:
                categories.append(term)
        return categories
    
    def _extract_arxiv_id(self, full_id):
        """Extract arXiv ID from full URL"""
        # Convert http://arxiv.org/abs/1234.5678v1 to 1234.5678
        if '/' in full_id:
            arxiv_id = full_id.split('/')[-1]
            # Remove version number if present
            if 'v' in arxiv_id:
                arxiv_id = arxiv_id.split('v')[0]
            return arxiv_id
        return full_id