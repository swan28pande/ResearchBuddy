import os
from langchain.chat_models import init_chat_model

class SummarizerAgent:
    def __init__(self):
        self.llm = init_chat_model("openai:gpt-4.1")

    def summarize(self, web_results, pub_results):
        def format_results(results):
            """Format results for LLM processing"""
            if not results:
                return "No results available"
            
            formatted = []
            for i, r in enumerate(results, 1):
                if isinstance(r, dict):
                    # Structured paper data from arXiv
                    title = r.get('title', 'Unknown Title')
                    abstract = r.get('abstract', 'No abstract available')
                    authors = r.get('authors', [])
                    authors_str = ', '.join(authors[:3])  # First 3 authors
                    if len(authors) > 3:
                        authors_str += f' et al. ({len(authors)} total)'
                    
                    formatted.append(
                        f"{i}. **{title}**\n"
                        f"   Authors: {authors_str}\n"
                        f"   Abstract: {abstract}\n"
                    )
                else:
                    # Fallback for non-structured data
                    formatted.append(f"{i}. {str(r)}")
            
            return "\n".join(formatted)

        prompt = (
            "Summarize the following web and publication results for a research report:\n\n"
            f"Web Results:\n{format_results(web_results)}\n\n"
            f"Publication Results:\n{format_results(pub_results)}"
        )
        try:
            response = self.llm.invoke(input=prompt)
            # Extract the summary content robustly
            if isinstance(response, dict) and "content" in response:
                return response["content"]
            elif hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as e:
            return f"Error generating summary: {e}"