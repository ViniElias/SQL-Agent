---
title: First Agent Template
emoji: ⚡
colorFrom: pink
colorTo: yellow
sdk: gradio
sdk_version: 5.15.0
app_file: app.py
pinned: false
tags:
- smolagents
- agent
- smolagent
- tool
- agent-course
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

## Passos para executar
### Crie o ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate     # Windows
```

### Instale as dependencias

```bash
pip install -r requirements.txt
```

### Instale o Ollama localmente e rode o comando 
```bash
ollama pull qwen2.5:3b
```

### Inicie o agente
```bash
python app.py
```