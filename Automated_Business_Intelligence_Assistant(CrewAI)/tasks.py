from crewai import Task
from tools import csv_tool
from agents import data_analyst_agent, business_consultant_agent

# Data Analyst Task
analyst_task = Task(
    description=(
        "Inspect and analyze the provided CSV dataset based on the given {topic}. "
        "Perform steps similar to data exploration in Python, such as: \n"
        "- Understanding column meanings and datatypes\n"
        "- Finding key descriptive statistics (mean, median, etc.)\n"
        "- Identifying trends, correlations, or anomalies\n"
        "- Grouping and summarizing data when relevant (e.g., by category, region, product)\n"
        "- Creating visualizations (e.g., bar charts, pie charts, scatter plots, heatmaps)\n\n"
        "Use analytical reasoning to derive meaningful insights that answer the user’s topic."
    ),
    expected_output=(
        "A structured analytical summary containing key findings, statistics, "
        "and generated visualization code or plots related to the {topic}."
    ),
    tools=[csv_tool],
    agent=data_analyst_agent,
    async_execution=False
)

# Data Visualization Task
consultant_task = Task(
    description=(
        "Take the findings from the Data Analyst and translate them into a clear and concise "
        "business summary. The summary should focus on:\n"
        "- The key takeaways from the analysis\n"
        "- The implications for business strategy, marketing, finance, or operations\n"
        "- Actionable recommendations for decision-makers\n"
        "- Any identified risks or opportunities.\n\n"
        "The tone should be professional and easily understandable for clients or management."
    ),
    expected_output=(
        "A polished business report summarizing the analytical results and providing "
        "recommendations in simple business terms."
    ),
    tools=[csv_tool],
    agent=business_consultant_agent,
    async_execution=False,
    output_file="business_summary.md"
)