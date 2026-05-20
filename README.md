# GenerativeAI-Projects

Welcome to my **Generative AI Projects** repository!
This repositoryy showcases **end-to-end Generative AI and LLM-based applications**, demonstrating how modern AI can automate reasoning, text understanding and decision-making tasks.

Each project focuses on practical, real-world applications of **LangChain**, **LangGraph**, **CrewAI** and **RAG Pipelines**, deployed with **Streamlit** for interactive use.

---

## Projects Overview

### 1. AI Ticket Traige System(LangGraph)

Automates the process of categorizing, summarizing, and routing healthcare support tickets using **LangGraph** and **Groq's LLM**.

The workflow intelligently classifies support issues, generated concise summaries, and assigns each ticket to the appropriate department - inproving efficiently and response time.

- Framework: LangGraph
- Model: Llama 3.1 8B (Groq API)  
- Deployment: Streamlit  
- [Project Link](AI_Ticket_Triage_System)

**Key Features**
- Classifies tickets into categories like Product Issue, Billing Issue, Login Issue, etc.
- Generates short summaries for each support ticket.
- Automatically routes isues to the correct department.
- Allows CSV upload and downloadable results.

---

### 2. Business Consultant Analyst (CrewAI)

**Business Consultant Analyst (CrewAI)** is an AI-powered analytics system that reads datasets, performs **Exploratory Data Analysis (EDA)**, generates **visualizations**, and produces **business summaries** with actionable insights.  

- Framework: CrewAI  
- Model: GPT-4o-mini  
- Deployment: Local Python environment  
- [Project Link](Business_Consultant_Analyst)

**Key Features**
- Automatically reads and analyzes any CSV dataset.  
- Performs statistical computations and correlation analysis.  
- Generates charts using Matplotlib, Seaborn, or Plotly.  
- Produces a professional **business insights summary report**.

**Technologies Used**
- Python 3.10  
- Pandas, NumPy for data handling  
- Matplotlib, Seaborn, Plotly for visualizations  
- CrewAI for agent orchestration  
- OpenAI LLM for generating insights  

---

### 3. QueryMyPDF

An intelligent **RAG (Retrieval-Augmented Generation)** system that allows users to **upload PDFs** and **interactively chat** with the document content.  
The app uses embeddings, vector storage, and conversational memory for accurate context-based question answering.

- Frameworks: LangChain, Pinecone  
- Models: Llama 3.1 (Groq), OpenAI Embeddings  
- Deployment: Streamlit  
- [Project Link](QueryMyPDF)

**Key Features**
- Upload multiple PDFs and query them conversationally.  
- Hybrid search using semantic (FAISS) and vector-based retrieval.  
- Maintains conversation history with contextual responses.  
- Built with **LangChain**, **Pinecone Vector Store**, and **Groq API**.

---

## Technologies & Libraries Used
- **Programming Language:** Python 3.10 
- **Frameworks & Tools:**  
  - `LangChain`, `LangGraph`, `CrewAI` – for building AI workflows  
  - `Groq API`, `OpenAI API` – for LLM model inference  
  - `FAISS`, `Pinecone` – for vector-based document retrieval  
  - `Streamlit` – for web app deployment  
  - `pandas`, `numpy`, `matplotlib`, `seaborn`, `plotly` – for data analysis and visualization  
  - `dotenv`, `tiktoken` – for environment and token management  
