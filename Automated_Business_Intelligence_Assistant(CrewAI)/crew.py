from crewai import Crew, Process
from agents import data_analyst_agent, business_consultant_agent
from tasks import analyst_task, consultant_task

crew = Crew(
    agents = [data_analyst_agent, business_consultant_agent],
    tasks = [analyst_task, consultant_task],
    process = Process.sequential,
    memory = True,
    cache = True,
    max_rpm = 100,
    share_crew = True
)

result = crew.kickoff(inputs = {'topic': "Which are the top 5 customer names with the highest total sales all over the data?"})
print(result)