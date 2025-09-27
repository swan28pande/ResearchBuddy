
from langchain.chat_models import init_chat_model

class PromptManagerAgent:
    def __init__(self):
        self.llm = init_chat_model("openai:gpt-4.1")

    def prompt_creation(self, query):
        prompt = ("The user has asked : "+query+" , Extract the relevant topic the user wants to know more and return the exact topic name the user want's to know")
        try:
            response = self.llm.invoke(input=prompt)
            if isinstance(response, dict) and "content" in response:
                print(response["content"])
                return response["content"]
            elif hasattr(response, "content"):
                print(response.content)
                return response.content
            return str(response)
        except Exception as e:
            return f"Error generating summary: {e}"