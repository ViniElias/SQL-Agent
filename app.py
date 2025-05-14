import requests
from bs4 import BeautifulSoup
import re
import gradio as gr
from sklearn.feature_extraction.text import TfidfVectorizer

def limpar_texto(texto):
    texto = re.sub(r'\[\d+.*?\]', '', texto)
    texto = re.sub(r'\[nota \d+\]', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\([^()]*ⓘ[^()]*\)', '', texto)
    texto = re.sub(r'\([^()]*escutar[^()]*\)', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def resumir_avancado(texto, n_sentencas=3):
    sentencas = [sent for sent in re.split(r'(?<=[.!?]) +', texto) if len(sent.split()) > 5]
    
    if len(sentencas) < 2:
        return texto
    
    try:
        vectorizer = TfidfVectorizer(stop_words='portuguese')
        X = vectorizer.fit_transform(sentencas)
        palavras_importantes = vectorizer.get_feature_names_out()
        
        nota_sentencas = []
        for i, sent in enumerate(sentencas):
            score = sum(X[i, vectorizer.vocabulary_[p]] for p in palavras_importantes if p in vectorizer.vocabulary_)
            nota_sentencas.append((sent, score))
        
        melhores = sorted(nota_sentencas, key=lambda x: x[1], reverse=True)[:n_sentencas]
        melhores = sorted(melhores, key=lambda x: sentencas.index(x[0]))
        resumo = ' '.join([s[0] for s in melhores])
        return resumo
    
    except:
        return texto[:1200] + "..." if len(texto) > 1200 else texto

def extrair_secoes_completas(soup):
    secoes = []
    current_section = {'titulo': 'Introdução', 'conteudo': []}
    
    # Encontra o início do conteúdo principal (depois do infobox)
    content = soup.find(id='mw-content-text')
    if not content:
        return []
    
    for elemento in content.find_all(['h2', 'h3', 'p']):
        if elemento.name in ['h2', 'h3']:
            if current_section['conteudo']:
                secoes.append(current_section)
            current_section = {
                'titulo': elemento.get_text().strip().replace('[editar]', ''),
                'conteudo': []
            }
        elif elemento.name == 'p' and elemento.get_text().strip():
            current_section['conteudo'].append(limpar_texto(elemento.get_text()))
    
    if current_section['conteudo']:
        secoes.append(current_section)
    
    return secoes

def formatar_resumo(secoes):
    if not secoes:
        return "Não foi possível extrair o conteúdo organizado por tópicos."
    
    resumo = ""
    for secao in secoes[:6]:  # Limita a 6 seções para não ficar muito longo
        if secao['conteudo']:
            texto_secao = ' '.join(secao['conteudo'][:3])  # Limita a 3 parágrafos por seção
            resumo_secao = resumir_avancado(texto_secao, n_sentencas=3)
            
            resumo += f"✦ {secao['titulo'].upper()} ✦\n"
            resumo += f"{resumo_secao}\n\n"
    
    return resumo.strip()

def buscar_e_resumir_por_topicos(titulo):
    titulo_formatado = titulo.strip().replace(" ", "_")
    url = f"https://pt.wikipedia.org/wiki/{titulo_formatado}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Página não encontrada na Wikipédia."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove elementos indesejados
        for element in soup.select('.mw-editsection, .reference, .noprint'):
            element.decompose()
        
        secoes = extrair_secoes_completas(soup)
        
        if not secoes:
            # Fallback para conteúdo básico
            conteudo = [limpar_texto(p.get_text()) for p in soup.select('p') if p.get_text().strip()]
            texto_completo = ' '.join(conteudo[:5000])
            return resumir_avancado(texto_completo, n_sentencas=7)
        
        return formatar_resumo(secoes)
    
    except Exception as e:
        return f"Ocorreu um erro ao processar: {str(e)}"

iface = gr.Interface(
    fn=buscar_e_resumir_por_topicos,
    inputs=gr.Textbox(label="Digite um tópico da Wikipédia", 
                     placeholder="Ex: Brasil, Inteligência Artificial..."),
    outputs=gr.Textbox(label="Resumo Organizado por Tópicos", lines=15),
    title="📚 WikiAgent - Resumo da Wikipedia por Tópicos",
    description="""Obtenha resumos estruturados de artigos da Wikipédia organizados por seções.""",
    examples=[["Brasil"], ["Inteligência Artificial"], ["Programação"]],
    css="""
        .gradio-container {max-width: full !important}
        .input_text textarea, .output_text textarea {font-size: 16px !important; line-height: 1.6 !important}
        h1 {text-align: center}
    """
)

iface.launch(share=False)