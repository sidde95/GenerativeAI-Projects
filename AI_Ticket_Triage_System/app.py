import os
import pandas as pd
import streamlit as st
from typing_extensions import TypedDict
from typing import Annotated
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize Groq LLM
llm = ChatGroq(model="llama-3.1-8b-instant")

# Defining Graph State 
class GraphState(TypedDict):
    ticket_text: str
    category: Annotated[str, "Predicted issue type"]
    summary: Annotated[str, "Ticket summary"]
    department: Annotated[str, "Department assigned"]

# Define Nodes
# Node 1: Ticket Classification
def ticket_classification(state: GraphState):
    ticket_text = state["ticket_text"]
    prompt = f"""
    Classify the following customer ticket into one of the categories:
    [Product Issue, Billing Issue, Appointment Scheduling, Login Issue, Reminder Problem, 
     Data Sync Error, Report Generation, General Inquiry].
    
    Ticket: {ticket_text}
    Only return the category name.
    """
    category = llm.invoke(prompt).content.strip()
    return {"ticket_text": ticket_text, "category": category, "summary": "", "department": ""}

# Node 2: Ticket Summarizer
def ticket_summarizer(state: GraphState):
    text = state["ticket_text"]
    prompt = f"Summarize this healthcare support ticket in less than 50 words:\n{text}"
    summary = llm.invoke(prompt).content.strip()
    return {"ticket_text": text, "category": state["category"], "summary": summary, "department": ""}

# Node 3: Department Routing 
def ticket_router(state:GraphState):
    category = state["category"]
    prompt = f""" Based on this ticket category: {category},
    route the tickets to most appropriate department who will solve this isse.
    Choose from departments : [Product Engineering, Finance, Customer Service, Technical Support, 
    Integrations Team, Analytics Team].
    
    Only return the department name"""
    department = llm.invoke(prompt).content.strip()
    return {"ticket_text": state["ticket_text"], "category": category, "summarizer": state["summary"], "department": department}



# Building Workflow
workflow = StateGraph(GraphState)
workflow.add_node("ticket_classification", ticket_classification)
workflow.add_node("ticket_summarizer", ticket_summarizer)
workflow.add_node("ticket_router", ticket_router)

workflow.add_edge(START, "ticket_classification")
workflow.add_edge("ticket_classification", "ticket_summarizer")
workflow.add_edge("ticket_summarizer", "ticket_router")
workflow.add_edge("ticket_router", END)

graph = workflow.compile()

# Setting up Streamlit UI
st.title("Healthcare Support Ticket Classifier")
st.write("""
         Upload a csv file containing healthcare support tickets.
         This app will automatically:
         1. Classify each ticket into a single category.
         2. Generate a short summary about the ticket.
         3. Let's you download the tagged results
         """)

uploaded_file = st.file_uploader("Upload CSV file (must have 'ticket_text' column)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "ticket_text" not in df.columns:
        st.error("Uploaded file must contain a 'ticket_text' column.")
    else:
        st.info(f"There are {df.shape[0]} issues in the uploaded file.")

        if st.button("Run Classification"):
            results = []

            for _, row in df.iterrows():  
                ticket_text = row["ticket_text"]
                input_state = {
                    "ticket_text": ticket_text,
                    "category": "",
                    "summary": "",
                    "ticket_router": ""
                }
                output = graph.invoke(input_state)
                results.append(output)

            result_df = pd.DataFrame(results)
            st.success("Classification and summarization complete ")

            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results", csv, "classified_tickets.csv", "text/csv")