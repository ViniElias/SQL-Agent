from typing import Any, Optional, Dict, List
from smolagents.tools import Tool
from dataclasses import dataclass
import textwrap

@dataclass
class ProductResult:
    title: str
    price: str
    store: str
    link: str

class FinalAnswerTool(Tool):
    name = "final_answer"
    description = "Provides a structured final answer to the given problem."
    inputs = {'answer': {'type': 'any', 'description': 'The final answer to the problem'}}
    output_type = "any"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_initialized = True

    def format_product_results(self, results: str) -> str:
        """Formats product price results into a clean, readable output."""
        if isinstance(results, str):
            if results.startswith("Erro") or "Nenhum resultado" in results:
                return results
            
            # Process the string format you're currently getting
            products = []
            current_product = {}
            for line in results.split('\n'):
                if '🛒' in line:
                    if current_product:
                        products.append(current_product)
                    current_product = {'title': line.replace('🛒', '').strip()}
                elif '💰' in line:
                    current_product['price'] = line.replace('💰 Preço:', '').strip()
                elif '🏪' in line:
                    current_product['store'] = line.replace('🏪 Loja:', '').strip()
                elif '🔗' in line:
                    current_product['link'] = line.replace('🔗 Link:', '').strip()
            
            if current_product:
                products.append(current_product)
            
            return self._format_as_table(products)
        return results

    def _format_as_table(self, products: List[Dict[str, str]]) -> str:
        """Formats product data as a clean table."""
        header = "📊 RESULTADOS ENCONTRADOS 📊"
        separator = "═" * 50
        rows = []
        
        for i, product in enumerate(products, 1):
            rows.append(
                f"\n🏷️ {i}. {product.get('title', 'N/A')}\n"
                f"💰 Preço: {product.get('price', 'N/A')}\n"
                f"🏪 Loja: {product.get('store', 'N/A')}\n"
                f"🔗 Link: {product.get('link', 'N/A') if product.get('link', 'N/A') != '#' else 'Indisponível'}\n"
                f"─" * 40
            )
        
        return (
            f"{header}\n"
            f"{separator}\n"
            f"{''.join(rows)}\n"
            f"\nℹ️ Dica: Sempre verifique o site da loja para confirmar disponibilidade e condições."
        )

    def forward(self, answer: Any) -> Any:
        if isinstance(answer, str) and ('🛒' in answer or '💰' in answer):
            return self.format_product_results(answer)
        return answer