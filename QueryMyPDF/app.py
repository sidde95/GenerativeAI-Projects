import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


HF_TOKEN = st.secrets["HF_TOKEN"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]
PINECONE_ENVIRONMENT = st.secrets.get("PINECONE_ENVIRONMENT", "us-east-1")

# Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Streamlit UI
st.title("Hybrid Search RAG Q&A with PDF")
st.write("Upload PDFs and chat with their content.")

# Groq API Key
api_key = st.text_input("Enter your Groq API Key:", type="password")

if api_key:
    llm = ChatGroq(groq_api_key=api_key, model="llama-3.1-8b-instant")

    # Memory store
    if "store" not in st.session_state:
        st.session_state.store = {}

    uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        all_docs = []
        for pdf in uploaded_files:
            with open("temp.pdf", "wb") as f:
                f.write(pdf.getvalue())
            loader = PyPDFLoader("temp.pdf")
            all_docs.extend(loader.load())

        # Split text
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        final_document = splitter.split_documents(all_docs)

        vectorstore = PineconeVectorStore.from_documents(final_document, 
                                                         embedding = embeddings, 
                                                         index_name=PINECONE_INDEX_NAME)
        retriever = vectorstore.as_retriever()

        # Prompt template
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Use the provided context to answer the user's question."
             "If the answer is not in the context, say you don't know.\n\nContext:\n{context}"),
             MessagesPlaceholder("chat_history"),
             ("human", "{input}")
             ])

        # Build chains
        question_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(retriever, question_chain)

        # Session history function
        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            if session_id not in st.session_state.store:
                st.session_state.store[session_id] = ChatMessageHistory()
            return st.session_state.store[session_id]

        # Runnable with memory
        conversational_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

        # User input
        session_id = st.text_input("Session ID:", value="default_session")
        user_question = st.text_input("Ask a question:")

        if user_question:
            session_history = get_session_history(session_id)
            response = conversational_chain.invoke(
                {"input": user_question},
                config={"configurable": {"session_id": session_id}}
            )
            st.write("Assistant:", response["answer"])
            st.write("Chat History:", session_history.messages)

else:
    st.warning("Please enter the Groq API Key.")