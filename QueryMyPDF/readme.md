# QueryMyPDF

**QueryMyPDF** is an AI-powered application built using **LangChain**, **Groq**, **Pinecone**, and **Streamlit**. It allows users to upload one or multiple PDF documents and interactively query their content through a chat-based interface. The app leverages a **Hybrid RAG (Retrieval-Augmented Generation)** pipeline to combine document retrieval with generative responses.

---

## Features

- Upload and process multiple PDF files.
- Retrieve relevant document chunks using **Pinecone Vector Store**.
- Generate contextual answers using **Groq’s LLaMA 3.1 8B model**.
- Persistent conversation memory for continuous context-aware dialogue.
- User authentication with secure key management using **Streamlit secrets**.
- Clean and interactive user interface powered by **Streamlit**.

---

## Tech Stack

| Component | Description |
|------------|-------------|
| **Streamlit** | Frontend UI for user interaction |
| **LangChain** | Framework for chaining LLM operations |
| **Groq API (LLaMA 3.1 8B Instant)** | Large language model for query answering |
| **Pinecone** | Vector database for document retrieval |
| **OpenAI Embeddings (text-embedding-3-small)** | Embeddings for vector representation of text |
| **PyPDFLoader** | PDF text extraction and processing |

---

## How It Works

1. **Upload PDFs** – Users upload one or multiple PDF documents.  
2. **Text Extraction** – The PDFs are parsed using `PyPDFLoader`.  
3. **Chunking** – The text is divided into smaller overlapping segments using `RecursiveCharacterTextSplitter`.  
4. **Embedding & Indexing** – Each chunk is embedded using OpenAI embeddings and stored in Pinecone.  
5. **Retrieval & Answering** – When a user asks a question:
   - The system retrieves the most relevant chunks from Pinecone.
   - The context is passed to Groq’s LLaMA model.
   - The model generates a concise, context-aware answer.
6. **Session Memory** – Each conversation maintains a chat history using LangChain’s `RunnableWithMessageHistory`.

---

## Usage
1. Enter your Groq API key in the provided field.
2. Upload one or multiple PDF files.
3. Enter a Session ID to maintain conversation history.
4. Ask questions about the context of your PDF's and get intelligent answers.

---

## Example Use Cases
1. Summarize lengthy research papers.
2. Extract key insights from reports.
3. Interactively query policy documents or manuals.
4. Build a knowledge assitant for internal company PDFs.

