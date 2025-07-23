import os
from langchain.chat_models import init_chat_model

class SummarizerAgent:
    def __init__(self):
        self.llm = init_chat_model("openai:gpt-4.1")

    def summarize(self, web_results, pub_results):
        def format_results(results):
            if isinstance(results, list):
                return "\n".join(f"- {str(r)}" for r in results)
            return str(results)

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