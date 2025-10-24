from dotenv import load_dotenv
import os

load_dotenv()  # Load .env
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  


from crewai_tools import CSVSearchTool

csv_tool = CSVSearchTool(csv = "sales_data_sample.csv")


