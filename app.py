from smolagents import CodeAgent,DuckDuckGoSearchTool, HfApiModel,load_tool,tool
import datetime
import requests
import pytz
import yaml
from tools.final_answer import FinalAnswerTool
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as psycopg2_connection
import json
from typing import List, Dict
from hf_token import HF_TOKEN

from Gradio_UI import GradioUI

os.environ["HF_TOKEN"] = HF_TOKEN


# Below is an example of a tool that does nothing. Amaze us with your creativity !
@tool
def my_custom_tool(arg1:str, arg2:int)-> str: #it's import to specify the return type
    #Keep this format for the description / args / args description but feel free to modify the tool
    """A tool that does nothing yet
    Args:
        arg1: the first argument
        arg2: the second argument
    """
    return "What magic will you build ?"

@tool
def get_current_time_in_timezone(timezone: str) -> str:
    """A tool that fetches the current local time in a specified timezone.
    Args:
        timezone: A string representing a valid timezone (e.g., 'America/New_York').
    """
    try:
        # Create timezone object
        tz = pytz.timezone(timezone)
        # Get current time in that timezone
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        return f"Error fetching time for timezone '{timezone}': {str(e)}"
    
@tool
def connect_to_db(database: str, user: str, password: str, host: str = "localhost", port: int = 5432) -> str:
    """Conecta ao banco de dados PostgreSQL e retorna a conexão.
    
    Args:
        database: Nome do banco de dados.
        user: Nome de usuário do banco de dados.
        password: Senha do usuário do banco de dados.
        host: Endereço do servidor do banco de dados.
        port: Porta do servidor do banco de dados (padrão é 5432 para PostgreSQL).
    """
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        return "Conexão com o banco de dados estabelecida com sucesso!"
    except Exception as e:
        return f"Erro ao conectar ao banco de dados: {str(e)}"
    
@tool
def create_table(database: str, user: str, password: str, host: str, port: int, table_name: str, columns: List[Dict[str, str]]) -> str:
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        column_definitions = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        query = sql.SQL("CREATE TABLE {} ({})").format(sql.Identifier(table_name), sql.SQL(column_definitions))
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return f"Tabela '{table_name}' criada com sucesso!"
    except Exception as e:
        return f"Erro ao criar a tabela '{table_name}': {str(e)}"
    
    
@tool
def insert_data(connection: psycopg2_connection, table_name: str, data: Dict[str, str]) -> str:
    """Insere dados em uma tabela do banco de dados.

    Args:
        connection: Conexão com o banco de dados.
        table_name: Nome da tabela.
        data: Dicionário contendo as colunas e os valores a serem inseridos.
    """
    try:
        cursor = connection.cursor()
        columns = ", ".join(data.keys())
        values = ", ".join([f"'{value}'" for value in data.values()])
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name), sql.SQL(columns), sql.SQL(values)
        )
        cursor.execute(query)
        connection.commit()
        cursor.close()
        return f"Dados inseridos na tabela '{table_name}' com sucesso!"
    except Exception as e:
        return f"Erro ao inserir dados na tabela '{table_name}': {str(e)}"
    
@tool
def read_data(connection: psycopg2_connection, table_name: str, columns: List[str]) -> str:
    """Lê dados de uma tabela do banco de dados.

    Args:
        connection: Conexão com o banco de dados.
        table_name: Nome da tabela.
        columns: Lista de colunas que deseja recuperar.
    """
    try:
        cursor = connection.cursor()
        columns_str = ", ".join(columns)
        query = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(columns_str), sql.Identifier(table_name)
        )
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        
        # Transformando a resposta em formato legível
        result_str = json.dumps(result, indent=2)
        return f"Dados lidos da tabela '{table_name}':\n{result_str}"
    except Exception as e:
        return f"Erro ao ler dados da tabela '{table_name}': {str(e)}"
    
@tool
def update_data(connection: psycopg2_connection, table_name: str, data: Dict[str, str], condition: str) -> str:
    """Atualiza dados em uma tabela do banco de dados.

    Args:
        connection: Conexão com o banco de dados.
        table_name: Nome da tabela.
        data: Dicionário contendo as colunas a serem atualizadas e os novos valores.
        condition: Condição para selecionar os registros a serem atualizados.
    """
    try:
        cursor = connection.cursor()
        set_clause = ", ".join([f"{col} = '{val}'" for col, val in data.items()])
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table_name), sql.SQL(set_clause), sql.SQL(condition)
        )
        cursor.execute(query)
        connection.commit()
        cursor.close()
        return f"Dados na tabela '{table_name}' atualizados com sucesso!"
    except Exception as e:
        return f"Erro ao atualizar dados na tabela '{table_name}': {str(e)}"
    
@tool
def delete_data(connection: psycopg2_connection, table_name: str, condition: str) -> str:
    """Exclui dados de uma tabela do banco de dados.

    Args:
        connection: Conexão com o banco de dados.
        table_name: Nome da tabela.
        condition: Condição para selecionar os registros a serem excluídos.
    """
    try:
        cursor = connection.cursor()
        query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table_name), sql.SQL(condition)
        )
        cursor.execute(query)
        connection.commit()
        cursor.close()
        return f"Dados na tabela '{table_name}' excluídos com sucesso!"
    except Exception as e:
        return f"Erro ao excluir dados da tabela '{table_name}': {str(e)}"



final_answer = FinalAnswerTool()

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

model = HfApiModel(
    max_tokens=2096,
    temperature=0.5,
    model_id='mistralai/Mistral-7B-Instruct-v0.2',
    custom_role_conversions=None,
)


# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=[DuckDuckGoSearchTool(), image_generation_tool], ## add your tools here (don't remove final answer)
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)


GradioUI(agent).launch()