import os
from langchain.chat_models import init_chat_model
from fpdf import FPDF


class ReportGeneratorAgent:
    def __init__(self):
        self.llm = init_chat_model("openai:gpt-4.1")

    def generate_report(self, query, summary, web_results, pub_results):
        def format_results(results, result_type="Results"):
            """Format results with proper structure and links"""
            if not results:
                return f"No {result_type.lower()} available"
            
            formatted = []
            for i, r in enumerate(results, 1):
                if isinstance(r, dict):
                    # Structured paper data from arXiv
                    title = r.get('title', 'Unknown Title')
                    authors = r.get('authors', [])
                    authors_str = ', '.join(authors[:3])
                    if len(authors) > 3:
                        authors_str += f' et al.'
                    
                    pdf_url = r.get('pdf_url', '')
                    arxiv_id = r.get('arxiv_id', '')
                    published = r.get('published', '')[:10]  # YYYY-MM-DD
                    abstract = r.get('abstract', 'No abstract available')
                    
                    entry = f"{i}. **{title}**\n"
                    if authors_str:
                        entry += f"   - Authors: {authors_str}\n"
                    if published:
                        entry += f"   - Published: {published}\n"
                    if arxiv_id:
                        entry += f"   - arXiv ID: {arxiv_id}\n"
                    if pdf_url:
                        entry += f"   - PDF: {pdf_url}\n"
                    entry += f"   - Abstract: {abstract[:300]}{'...' if len(abstract) > 300 else ''}\n"
                    
                    formatted.append(entry)
                else:
                    # Fallback for non-structured data
                    formatted.append(f"{i}. {str(r)}")
            
            return "\n".join(formatted)

        prompt = (
            f"Generate a detailed research report for the query: '{query}'.\n\n"
            f"Summary:\n{summary}\n\n"
            f"Web Results:\n{format_results(web_results, 'Web Results')}\n\n"
            f"Publication Results:\n{format_results(pub_results, 'Academic Publications')}\n\n"
            "Format the report with sections, each section should have the link of its reference link, overall citations, and a conclusion. Give a Table of Contents but without links."
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

    # def save_report_as_pdf(self, report_text, filename="report.pdf"):
    #     pdf = FPDF()
    #     pdf.add_page()
    #     pdf.set_auto_page_break(auto=True, margin=15)
    #     pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.sfd', uni=True)
    #     pdf.set_font('DejaVu', '', 12)
    #     for line in report_text.split('\n'):
    #         pdf.cell(0, 10, self.clean_text(line), ln=True)
    #     pdf.output(filename)
    #     return filename

    # def clean_text(self, text):
    #     # Replace em-dash and other common unicode with ASCII equivalents
    #     return text.replace('\u2014', '-').encode('latin-1', 'ignore').decode('latin-1')