from crewai import Agent
from tools import csv_tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
import os

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# Data Analyst Agent

data_analyst_agent = Agent(
    role="Data Analyst",
    goal=(
        "Perform exploratory data analysis (EDA) on the provided CSV dataset. "
        "Understand its structure, summarize key statistics, detect missing or anomalous values, "
        "and find insights relevant to the topic provided by the user. "
        "Perform computations such as grouping, aggregations, correlations, and visualizations "
        "to highlight trends or patterns."
    ),
    backstory=(
        "A data analytics expert proficient in Python (Pandas, NumPy, Matplotlib, Seaborn, Plotly). "
        "Can independently explore any tabular dataset to find trends, patterns, KPIs, or outliers "
        "and produce meaningful summaries and charts."
    ),
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.5),
    verbose=True,
    memory=True,
    tools=[csv_tool],
    allow_delegation=True
)


# Visualization Agent
business_consultant_agent = Agent(
    role="Business Consultant",
    goal=(
        "Interpret the analytical results from the Data Analyst and transform them into "
        "a high-level business summary suitable for decision-makers. "
        "Provide insights, recommendations, and strategic implications based on the findings."
    ),
    backstory=(
        "A business consultant skilled at translating complex analytical insights into "
        "clear, actionable recommendations. Understands business KPIs, customer behavior, "
        "and strategic planning across industries."
    ),
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.6),
    verbose=True,
    memory=True,
    tools=[csv_tool],
    allow_delegation=False
)
