from crewai import Task
from tools import python_tool
from agents import data_analyst_agent, business_consultant_agent

# Data Analyst Task
analyst_task = Task(
    description=(
        "Read the provided CSV dataset. Using Python (pandas), perform the following for {topic}: \n"
        "- Compute total sales grouped by YEAR_ID and PRODUCTLINE\n"
        "- Identify top selling and least selling products per year\n"
        "- Generate summary tables and visualizations\n\n"
        "IMPORTANT:\n"
        "- Assign all final outputs (dataframes and plots) to a single dictionary called 'result'\n"
        "- Save plots to files (e.g., 'sales_plot.png') instead of using plt.show()\n"
        "- Print the 'result' dictionary at the end"
    ),
    expected_output=(
        "A dictionary named 'result' containing: \n"
        "- grouped_data: list of dicts\n"
        "- highest_selling: list of dicts\n"
        "- least_selling: list of dicts\n"
        "- plot_file: filename of saved plot"
    ),
    tools=[python_tool],
    agent=data_analyst_agent,
    async_execution=False
)

# Business Consultant Task
consultant_task = Task(
    description=(
        "Take the 'result' dictionary from the Data Analyst and create a clear business summary. "
        "Focus on key takeaways, implications for strategy, actionable recommendations, "
        "and any identified risks or opportunities. Include references to the plots."
    ),
    expected_output=(
        "A polished business report summarizing the analytical results "
        "and providing recommendations in simple business terms."
    ),
    agent=business_consultant_agent,
    async_execution=False,
    output_file="business_summary.md"
)
