import ollama
from smolagents import CodeAgent, tool
from tools.final_answer import FinalAnswerTool
from Gradio_UI import GradioUI
import yaml
from transformers import pipeline
import requests

# Model Wrapper
class OllamaModelWrapper:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, **kwargs):
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": str(prompt)}]
        )

        if 'text' in response:
            return response['text']
        elif 'message' in response:
            return response['message']
        else:
            return "Unexpected response format"

    def __call__(self, prompt: str, **kwargs):
        return self.generate(prompt, **kwargs)

# Final Answer Tool
final_answer = FinalAnswerTool()

# Tool: Buscar preços de produtos
@tool
def search_prices_serpapi(product_name: str) -> str:
    """
    Searches for product prices on Google Shopping using SerpAPI.
    
    Args:
        product_name (str): The name of the product to search for (e.g. "iPhone 13 Pro")
        
    Returns:
        str: A formatted string containing product information including:
            - Title
            - Price
            - Store
            - Link
            
    Example:
        >>> search_prices_serpapi("iPhone 13 Pro")
        '📱 Apple iPhone 13 Pro 128GB💰 Preço: R$ 5.499,00🏪 Loja: Magazine Luiza🔗 https://example.com'
        
    Raises:
        Exception: If there's an error with the API request or response parsing
    """
    try:
        API_KEY = "b22ab4f321d68d5e5b17d298396e555de3b232beafe03d229b9860afc01257f8"
        params = {
            "engine": "google_shopping",
            "q": product_name,
            "hl": "pt-br",
            "gl": "br",
            "api_key": API_KEY
        }

        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        if "shopping_results" not in data:
            return "Nenhum resultado encontrado."

        results = []
        for item in data["shopping_results"][:5]:  # Limita a 5 resultados
            title = item.get("title", "Sem título")
            
            # Filtra resultados não relevantes
            if product_name.split()[0].lower() not in title.lower():
                continue
                
            price = item.get("price", "Preço não disponível")
            link = item.get("link", "Link não disponível") 
            source = item.get("source", "Loja desconhecida")
            
            results.append(
                f"<br/>📱 {title}<br/>"
                f"💵 Preço: {price}<br/>"
                f"🏬 Loja: {source}<br/>"
                f"🔗 {link}<br/>"
                f"―――――――――――――――――――"
            )

        return "<br/>".join(results) if results else "Nenhum resultado relevante encontrado."

    except Exception as e:
        return f"Erro na busca: {str(e)}"

# Carrega templates
with open("prompts.yaml", 'r', encoding='utf-8') as stream:
    prompt_templates = yaml.safe_load(stream)

# Inicializa modelo e agente 
model = OllamaModelWrapper(model_name="qwen2.5:3b")

agent = CodeAgent(
    model=model,
    tools=[final_answer, search_prices_serpapi],
    max_steps=6,
    verbosity_level=1,
    prompt_templates=prompt_templates
)

# Interface
GradioUI(agent).launch()
