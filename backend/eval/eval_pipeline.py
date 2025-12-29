import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from workflows.research_workflow import build_and_run_workflow, ResearchState
from langgraph.graph import StateGraph, START, END

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class LLMJudge:
    def __init__(self, model_name="gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert research evaluator. Your task is to evaluate a generated research report based on a query and retrieved sources."),
            ("user", """
Evaluate the following research report based on the criteria below. 
Provide a score from 1-5 for each criterion and a brief justification.

Query: {query}

Retrieved Sources Summary: {summary}

Generated Report:
{report}

Criteria:
1. Faithfulness: Is the report grounded in the retrieved sources? (1-5)
2. Answer Relevancy: How well does the report address the query? (1-5)
3. Formatting: Does the report include a Table of Contents and proper citations/links? (1-5)

Output your response in JSON format like this:
{{
    "scores": {{
        "faithfulness": 0,
        "relevancy": 0,
        "formatting": 0
    }},
    "justification": "..."
}}
""")
        ])

    def evaluate(self, query: str, summary: str, report: str) -> Dict:
        chain = self.prompt | self.llm
        response = chain.invoke({
            "query": query,
            "summary": summary,
            "report": report
        })
        try:
            # Handle potential JSON parsing issues
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse judge output: {e}\nRaw output: {response.content}")
            return {"error": str(e), "raw": response.content}

def run_evaluation():
    # Load Golden Dataset
    eval_dir = os.path.dirname(__file__)
    dataset_path = os.path.join(eval_dir, "golden_dataset.json")
    
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    judge = LLMJudge()
    results = []

    print(f"\n--- Starting Evaluation of {len(dataset)} Queries ---\n")

    for entry in dataset:
        query = entry["query"]
        logger.info(f"Evaluating query: {query}")

        # In a real scenario, we might want to capture the intermediate state (summary/sources)
        # For now, we'll modify the workflow slightly or just run it and take the final report.
        # But wait, the judge needs the sources to check faithfulness.
        
        # Let's modify build_and_run_workflow to optionally return the full state
        # instead of just the report if needed, or just run its components.
        
        # For simplicity in this demo script, I'll use a modified version of the workflow execution
        # to get both the summary (sources) and the final report.
        
        try:
            # We need to import the internal components to get the state
            from agents.prompt_manager import PromptManagerAgent
            from agents.internet_search import InternetSearchAgent
            from agents.publication_search import PublicationSearchAgent
            from agents.summarizer import SummarizerAgent
            from agents.report_generator import ReportGeneratorAgent
            from api_clients.tavily import TavilyClient
            from api_clients.arxiv import ArxivClient

            tavily_client = TavilyClient(os.getenv("TAVILY_API_KEY"))
            arxiv_client = ArxivClient()
            
            prompt_manager = PromptManagerAgent()
            internet_agent = InternetSearchAgent(tavily_client)
            pub_agent = PublicationSearchAgent([arxiv_client])
            summarizer = SummarizerAgent()
            reporter = ReportGeneratorAgent()

            # Execute step by step for evaluation
            prompt_results = prompt_manager.prompt_creation(query)
            web_results = internet_agent.search(prompt_results)
            pub_results = pub_agent.search(prompt_results)
            summary = summarizer.summarize(web_results, pub_results)
            report = reporter.generate_report(prompt_results, summary, web_results, pub_results)

            # Evaluate
            evaluation = judge.evaluate(query, summary, report)
            
            results.append({
                "id": entry["id"],
                "query": query,
                "category": entry.get("category"),
                "scores": evaluation.get("scores"),
                "justification": evaluation.get("justification")
            })
            
            print(f"Query: {query}")
            print(f"Scores: {evaluation.get('scores')}")
            print("-" * 30)

        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            results.append({
                "id": entry["id"],
                "query": query,
                "error": str(e)
            })

    # Save results
    results_path = os.path.join(eval_dir, "eval_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nEvaluation complete. Results saved to {results_path}")

if __name__ == "__main__":
    run_evaluation()
