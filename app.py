#!/usr/bin/env python
# coding=utf-8
# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import pytz
import yaml
import os
from typing import Any

from smolagents.agents import MultiStepAgent, ActionStep
from smolagents.memory import MemoryStep
from smolagents.tools import tool
from smolagents.agent_types import AgentText, AgentImage, AgentAudio, handle_agent_output_types
from browser_use import Agent
from Gradio_UI import GradioUI
from ollama import Client

# Example custom tool
@tool
def my_custom_tool(arg1: str, arg2: int) -> str:
    """A tool that does nothing yet

    Args:
        arg1: the first argument
        arg2: the second argument

    Returns:
        A placeholder string."""
    return "What magic will you build?"

@tool
def get_current_time_in_timezone(timezone: str) -> str:
    """Fetches the current local time in a specified timezone.

    Args:
        timezone: A string representing a valid timezone (e.g., 'America/New_York').

    Returns:
        A formatted string with the local time in the given timezone."""
    try:
        tz = pytz.timezone(timezone)
        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current local time in {timezone} is: {local_time}"
    except Exception as e:
        return f"Error fetching time for timezone '{timezone}': {e}"

@tool
def comparar_produto_online(nome_produto: str) -> str:
    """Compara preços de um produto em diferentes sites usando navegação automatizada.

    Args:
        nome_produto: Nome do produto a ser pesquisado e comparado.

    Returns:
        Uma string agregada contendo trechos dos resultados de busca de cada site."""
    try:
        browser = Agent()
        sites = {
            "OLX": f"https://www.olx.com.br/buscar?q={nome_produto}",
            "Buscapé": f"https://www.buscape.com.br/search?q={nome_produto}",
            "Magazine Luiza": f"https://www.magazineluiza.com.br/busca/{nome_produto}"
        }

        resultados = []
        for nome_site, url in sites.items():
            browser.goto(url)
            browser.wait_for_element("body")
            page_content = browser.page_content
            resultados.append(f"--- {nome_site} ---\n{page_content[:500]}...")

        browser.close()
        return "\n\n".join(resultados)

    except Exception as e:
        return f"Erro ao comparar produto '{nome_produto}': {e}"

class OllamaAgent(MultiStepAgent):
    """
    Agente que usa o Ollama para gerar respostas.
    """
    def _step_stream(self, memory_step: MemoryStep):
        """
        For streaming: delegate to the synchronous step implementation.
        """
        result = self.step(memory_step)
        yield result
    """
    Agente que usa o Ollama para gerar respostas.
    """
    def __init__(self, ollama_model: str = "llama2", **kwargs: Any):
        super().__init__(model=None, **kwargs)
        self.ollama_client = Client()
        self.ollama_model = ollama_model

    def step(self, step_log: MemoryStep) -> MemoryStep:
        if not isinstance(step_log, ActionStep):
            return step_log

        llm_input = self.format_prompt(step_log)
        response = self.ollama_client.generate(model=self.ollama_model, prompt=llm_input)
        llm_response = response.get("response", "")
        step_log.model_output = llm_response
        return step_log

    def initialize_system_prompt(self) -> str:
        return "Você é um assistente útil."

    def format_prompt(self, step_log: ActionStep) -> str:
        prompt = ""
        if getattr(step_log, 'thought', None):
            prompt += f"Thought: {step_log.thought}\n"
        if getattr(step_log, 'tool_calls', None):
            for tool_call in step_log.tool_calls:
                prompt += f"Action: {tool_call.name}({tool_call.arguments})\n"
        prompt += "Observation: "
        return prompt

# Import DuckDuckGoSearchTool if available
try:
    from smolagents.tools import DuckDuckGoSearchTool
    duckduckgo_tool = DuckDuckGoSearchTool()
except ImportError:
    duckduckgo_tool = None
    print("DuckDuckGoSearchTool não encontrado; continue sem ela.")

# Define image_generation_tool como None
image_generation_tool = None

# Carrega prompts
template_path = os.path.join(os.path.dirname(__file__), "prompts.yaml")
with open(template_path, "r") as stream:
    prompt_templates = yaml.safe_load(stream)

# Lista de ferramentas
tools = [
    t for t in (duckduckgo_tool, image_generation_tool, comparar_produto_online) if t
]

# Inicializa o agente e a UI
agent = OllamaAgent(
    ollama_model="llama2",
    tools=tools,
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates,
)

GradioUI(agent).launch()
