# ResearchBuddy

An AI-powered multi-agent research assistant that automates deep literature reviews and report generation using language models and orchestration.

## Features

- **Multi-Agent Architecture**: Coordinated agents for internet search, academic publication retrieval, summarization, and report generation
- **Advanced LLM Integration**: Leverages OpenAI GPT-4 for intelligent summarization and natural language report writing
- **Academic Search**: Integrates with Semantic Scholar and arXiv APIs for comprehensive literature review
- **Web Search**: Uses Tavily API for real-time web information gathering
- **PDF Report Generation**: Automatically generates professional research reports in PDF format
- **Modern Web Interface**: Clean, responsive React frontend built with Vite
- **RESTful API**: Flask-based backend with CORS support for seamless frontend integration

## Tech Stack

### Backend
- Python 3.11+
- LangGraph
- LangChain
- OpenAI GPT-4 
- Flask
- FPDF

### Frontend
- React 18 
- Vite 

### APIs & Services
- Semantic Scholar API 
- arXiv API 
- Tavily API 

## Prerequisites

- Python 3.11 or higher
- Node.js 16 or higher
- npm or yarn
- OpenAI API key
- Tavily API key (optional, for web search)
- Semantic Scholar API key (optional, for academic search)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ResearchBuddy.git
cd ResearchBuddy
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

## 🔧 Configuration

Create a `.env` file in the backend directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key_here
```

## Usage

### 1. Start the Backend
```bash
cd backend
python app.py
```
The API will be available at `http://localhost:8000`

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:5173`

### 3. Using the Application
1. Open your browser and navigate to `http://localhost:5173`
2. Enter your research query in the input field
3. Click "Generate Report" to start the research process
4. Wait for the agents to complete their tasks
5. Download the generated PDF report

## Project Structure

```
ResearchBuddy/
├── backend/
│   ├── agents/                 # Multi-agent system
│   │   ├── coordinator.py      # Workflow coordinator
│   │   ├── internet_search.py  # Web search agent
│   │   ├── publication_search.py # Academic search agent
│   │   ├── summarizer.py       # Content summarization agent
│   │   └── report_generator.py # Report generation agent
│   ├── api_clients/            # External API integrations
│   │   ├── tavily.py          # Web search API client
│   │   ├── semantic_scholar.py # Academic search API client
│   │   └── arxiv.py           # arXiv API client
│   ├── workflows/              # LangGraph workflows
│   │   └── research_workflow.py # Main research workflow
│   ├── app.py                 # Flask application
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.jsx           # Main application component
│   │   └── main.jsx          # Application entry point
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Workflow

1. **User Input**: User submits a research query through the web interface
2. **Agent Coordination**: LangGraph orchestrates the multi-agent workflow
3. **Parallel Search**: Internet and publication search agents run simultaneously
4. **Content Summarization**: Summarizer agent processes and synthesizes findings
5. **Report Generation**: Report generator creates a comprehensive research report
6. **PDF Export**: Report is automatically converted to PDF format
7. **User Delivery**: User receives both text and PDF versions of the report

## API Endpoints

### POST `/api/research`
Generate a research report for a given query.

**Request Body:**
```json
{
  "query": "Recent advances in quantum computing"
}
```

**Response:**
```json
{
  "report": "Generated research report text...",
  "pdf_url": "/api/pdf/research_report.pdf"
}
```

### GET `/api/pdf/<filename>`
Download a generated PDF report.
