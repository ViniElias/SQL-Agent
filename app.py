from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel, load_tool, tool
import yaml
from tools.final_answer import FinalAnswerTool
from tools.mysqltools import (
    mysql_connect, mysql_execute, mysql_fetch,
    mysql_connect_tool, mysql_exec_tool, mysql_fetch_tool
)
import os
from hf_token import HF_TOKEN

from Gradio_UI import GradioUI

os.environ["HF_TOKEN"] = HF_TOKEN

final_answer = FinalAnswerTool()

model = HfApiModel(
    max_tokens=2096,
    temperature=0.5,
    model_id='Qwen/Qwen2.5-Coder-32B-Instruct',
    custom_role_conversions=None,
)

# Import image generation tool
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)

def execute_sql_script(conn, filepath):
    """Reads and executes SQL commands from a file"""
    with open(filepath, 'r') as file:
        sql_script = file.read()
        for statement in sql_script.split(';'):
            stmt = statement.strip()
            if stmt:
                mysql_execute(conn, stmt)

agent = CodeAgent(
    model=model,
    tools=[
        DuckDuckGoSearchTool(),
        image_generation_tool,
        mysql_connect_tool,
        mysql_exec_tool,
        mysql_fetch_tool,
        final_answer
    ],
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)

# Conexão com o banco
conn = mysql_connect("localhost", "root", "senha123", "escola")

# Scripts para criação da estrutura e dados iniciais
execute_sql_script(conn, "setup_escola.sql")

# Executar comandos e buscar resultados
mysql_execute(conn, "INSERT INTO aluno (nome,idade) VALUES (%s,%s)", ("Maria", 22))
rows = mysql_fetch(conn, "SELECT nome, idade FROM aluno")
print(rows)

# Launch UI
GradioUI(agent).launch()