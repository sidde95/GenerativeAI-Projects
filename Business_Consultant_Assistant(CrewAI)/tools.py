from dotenv import load_dotenv
import os
from crewai_tools import CodeInterpreterTool

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  

# Attach CSV file path here
python_tool = CodeInterpreterTool(csv="sales_data_sample.csv")
