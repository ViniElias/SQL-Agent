import re
import subprocess
import json
import gradio as gr
from playwright.sync_api import sync_playwright

# --- Scraping Function for Amazon Reviews using Playwright ---
def scrape_amazon_reviews(product_url: str, pages: int = 2):
    """
    Extrai o ASIN da URL da Amazon e faz scraping das páginas de reviews via Playwright.
    Retorna lista de textos das avaliações.
    """
    # Extrai ASIN (10 caracteres alfanuméricos)
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", product_url)
    if not m:
        raise ValueError("Não foi possível extrair o ASIN da URL fornecida.")
    asin = m.group(1)

    all_reviews = []
    review_template = (
        "https://www.amazon.com.br/product-reviews/{asin}/"
        "ref=cm_cr_arp_d_viewpnt?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1"
            ),
        )
        page = context.new_page()

        for page_num in range(1, pages + 1):
            url = review_template.format(asin=asin, page=page_num)
            page.goto(url, timeout=60000, wait_until='networkidle')
            try:
                page.wait_for_selector('div[data-hook="review"]', timeout=10000)
            except:
                break
            # coleta containers de review
            containers = page.query_selector_all('div[data-hook="review"]')
            for c in containers:
                # extrai texto principal
                elem = c.query_selector('span[data-hook="review-body"] span')
                if elem:
                    text = elem.inner_text().strip()
                    if text:
                        all_reviews.append(text)

        context.close()
        browser.close()

    return all_reviews

# --- LLM Analysis Function ---
def analyze_with_ollama(reviews):
    prompt = (
        "Você é um analista de produtos. "
        "Com base nas análises dos clientes a seguir, liste os pontos fortes e fracos do produto.\n\n"
        + "\n\n".join(f"- {r}" for r in reviews[:20])
    )
    proc = subprocess.run([
        "ollama", "run", "qwen2.5:3b",
        "--prompt", prompt,
        "--json"
    ], capture_output=True, text=True)
    if proc.returncode != 0:
        return f"Erro na análise: {proc.stderr}"
    try:
        out = json.loads(proc.stdout)
        return out.get('text', '').strip()
    except json.JSONDecodeError:
        return "Resposta do modelo inválida."

# --- Orchestration for Gradio ---
def analyze_reviews_amazon(amz_url: str):
    if not amz_url:
        return "Por favor, insira uma URL válida da Amazon."
    try:
        reviews = scrape_amazon_reviews(amz_url, pages=2)
    except Exception as e:
        return f"Erro ao coletar reviews: {e}"
    if not reviews:
        return "Nenhuma avaliação encontrada para este produto."
    return analyze_with_ollama(reviews)

# --- Gradio Interface ---
with gr.Blocks(title="Analisador de Reviews Amazon") as demo:
    gr.Markdown("## Análise de Pontos Fortes e Fracos de Produtos na Amazon")
    amz_input = gr.Textbox(
        label="URL do produto Amazon",
        placeholder="https://www.amazon.com.br/dp/B08XXXXXXX"
    )
    output = gr.Textbox(label="Resultado da análise", lines=15)
    analyze_btn = gr.Button("Analisar")

    analyze_btn.click(
        fn=analyze_reviews_amazon,
        inputs=[amz_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()