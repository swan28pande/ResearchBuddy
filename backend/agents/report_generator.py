import os
from langchain.chat_models import init_chat_model
from fpdf import FPDF


class ReportGeneratorAgent:
    def __init__(self):
        self.llm = init_chat_model("openai:gpt-4.1")

    def generate_report(self, query, summary, web_results, pub_results):
        def format_results(results):
            if isinstance(results, list):
                return "\n".join(f"- {str(r)}" for r in results)
            return str(results)

        prompt = (
            f"Generate a detailed research report for the query: '{query}'.\n\n"
            f"Summary:\n{summary}\n\n"
            f"Web Results:\n{format_results(web_results)}\n\n"
            f"Publication Results:\n{format_results(pub_results)}\n\n"
            "Format the report with sections, citations, and a conclusion."
        )
        try:
            response = self.llm.invoke(input=prompt)
            # Extract the content if response is a message object or dict
            if isinstance(response, dict) and "content" in response:
                return response["content"]
            elif hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as e:
            return f"Error generating report: {e}"

    def save_report_as_pdf(self, report_text, filename="report.pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in report_text.split('\n'):
            pdf.cell(0, 10, line, ln=True)
        pdf.output(filename)
        return filename