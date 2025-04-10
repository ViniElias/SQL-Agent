from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel, load_tool, tool
import requests
import pytz
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine, insert, inspect, text
import yaml
from tools.final_answer import FinalAnswerTool
import os
from hf_token import HF_TOKEN

from Gradio_UI import GradioUI

os.environ["HF_TOKEN"] = HF_TOKEN

# Criação do BD na memória
engine = create_engine("sqlite:///:memory:")
metadata_obj = MetaData()

# Criação da tabela e colunas
table_name = "receipts"
receipts = Table(
    table_name,
    metadata_obj,
    Column("receipt_id", Integer, primary_key=True),
    Column("customer_name", String(16)),
    Column("price", Float)
)
metadata_obj.create_all(engine)

rows = [
    {"receipt_id": 1, "customer_name": "Alan Payne", "price": 12.06},
    {"receipt_id": 2, "customer_name": "Alex Mason", "price": 23.86},
    {"receipt_id": 3, "customer_name": "Woodrow Wilson", "price": 53.43},
    {"receipt_id": 4, "customer_name": "Margaret James", "price": 21.11},
]
for row in rows:
    stmt = insert(receipts).values(**row)
    with engine.begin() as connection:
        cursor = connection.execute(stmt)

inspector = inspect(engine)
columns_info = [(col["name"], col["type"]) for col in inspector.get_columns("receipts")]

table_description = "Columns:\n" + "\n".join([f"  - {name}: {col_type}" for name, col_type in columns_info])
print(table_description)

@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the table. Returns a string representation of the result.
    The table is named 'receipts'. Its description is as follows:
        Columns:
        - receipt_id: INTEGER
        - customer_name: VARCHAR(16)
        - price: FLOAT
    Args:
        query: The query to perform. This should be correct SQL.
    """
    output = ""
    with engine.connect() as con:
        rows = con.execute(text(query))
        for row in rows:
            output += "\n" + str(row)
    return output

final_answer = FinalAnswerTool()

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

model = HfApiModel(
max_tokens=2096,
temperature=0.5,
model_id='Qwen/Qwen2.5-Coder-32B-Instruct',# it is possible that this model may be overloaded
custom_role_conversions=None,
)

# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=[DuckDuckGoSearchTool(), sql_engine, image_generation_tool], ## add your tools here (don't remove final answer)
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)

GradioUI(agent).launch()
# agent.run("Can you give me the name of the client who got the most expensive receipt?")