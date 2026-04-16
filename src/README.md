## Estrutura 

```
src/
├── app.py              # Interface principal do Streamlit e fluxo do chat
├── rag.py              # Lógica de vetorização e busca no dataset (TF-IDF)
└── requirements.txt    # Dependências do Python
```

## Exemplo de requirements.txt

```
streamlit>=1.35.0
ollama>=0.2.0
datasets>=2.19.0
scikit-learn>=1.4.0
numpy>=1.26.0
pandas>=2.0.0
PyPDF2>=3.0.0
```

## Como Rodar

```bash
#clonar
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio/src

# Instalar dependências
pip install -r requirements.txt

#iniciar ollama
ollama serve

# Rodar a aplicação
streamlit run app.py
```
