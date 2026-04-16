import streamlit as st
import ollama
import pandas as pd
import PyPDF2
from rag import FinanceRAG

st.set_page_config(
    page_title="Consultor Financeiro IA",
    page_icon="💸",
    layout="wide",
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a472a, #2d6a4f);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }
    .tip-box {
        background: #f0faf4;
        border-left: 4px solid #2d6a4f;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #1a3a2a;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>💸 Consultor Financeiro IA</h1>
    <p>Powered by Gemma 4 (local) · Base: Finance-Instruct-500k</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configurações")

    model_name = st.selectbox(
        "Modelo Ollama",
        ["gemma4:e4b", "gemma4:e2b"],
        index=0,
    )

    use_rag = st.toggle("Usar base de dados financeira (RAG)", value=True)
    n_examples = st.slider("Exemplos do dataset", 1, 5, 2) if use_rag else 0

    st.divider()
    st.markdown("###  O que posso te ajudar?")
    st.markdown("""
- 📊 Organizar seu orçamento mensal
- 💰 Estratégias para poupar dinheiro
- 📈 Explicar investimentos (renda fixa, ações, fundos)
- 🏦 Diferença entre produtos financeiros
- 💳 Controle de dívidas e cartão de crédito
- 🎯 Planejamento de metas financeiras
- 📉 Entender inflação, juros, câmbio
""")
    st.divider()

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

    st.caption("🔒 Tudo roda localmente. Seus dados não saem do seu computador.")

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="tip-box">
    💡 <strong>Dica:</strong> Seja específico para melhores respostas.<br>
    Ex: <em>"Ganho R$3.000/mês, gasto R$1.200 de aluguel e quero juntar R$10.000 em 1 ano. Como organizo?"</em>
    </div>
    """, unsafe_allow_html=True)

@st.cache_resource(show_spinner="📚 Carregando base de dados financeira...")
def load_rag():
    rag = FinanceRAG()
    rag.load_dataset()
    return rag

rag = load_rag()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Olá! Eu sou o **T.H.E.O.** (Tecnologia de Hábitos e Economia Orçamentária). Como posso te ajudar com suas finanças hoje?"
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt_data := st.chat_input("Pergunte algo ou anexe um arquivo financeiro...", accept_file=True, file_type=["pdf", "csv", "xlsx"]):
    
   
    texto_usuario = prompt_data.text
    arquivos_usuario = prompt_data.files
    
    contexto_do_arquivo = ""
    
   
    if arquivos_usuario:
        arquivo = arquivos_usuario[0]
        contexto_do_arquivo = process_file(arquivo) # Chama a função que extrai o texto
        st.toast(f"📄 O Theo acabou de ler sua planilha/PDF: {arquivo.name}")
        
       
        if not texto_usuario:
            texto_usuario = f"Por favor, analise os dados deste arquivo: {arquivo.name}"

   
    if not texto_usuario:
        st.stop()

    
    st.session_state.messages.append({"role": "user", "content": texto_usuario})
    with st.chat_message("user"):
        st.markdown(texto_usuario)

    context_block = ""
    
    
    if contexto_do_arquivo:
       
        context_block += f"\n---\n[DADOS DO ARQUIVO ENVIADO PELO USUÁRIO]\n{contexto_do_arquivo[:2000]}\n---\n"

    
    if use_rag:
        examples = rag.search(texto_usuario, k=n_examples)
        if examples:
            context_block += "\n---\nExemplos de referência da base financeira:\n"
            for i, ex in enumerate(examples, 1):
                context_block += f"\n[{i}] Pergunta: {ex['instruction']}\nResposta: {ex['output'][:400]}...\n"
            context_block += "---\n"

  
    system_prompt = """Você é o T.H.E.O. (Tecnologia de Hábitos e Economia Orçamentária), um consultor financeiro pessoal experiente,amigavel e didático.
    
Seu papel é:
- Ajudar o usuário a organizar suas finanças pessoais de forma prática
- Explicar conceitos financeiros de forma clara e acessível
- Sugerir estratégias de economia, investimento e controle de dívidas
- Criar planos financeiros personalizados quando o usuário fornecer seus dados (salário, gastos, metas)
- Responder sempre em português do Brasil, de forma acolhedora e objetiva

Diretrizes importantes:
- Nunca invente rendimentos garantidos — sempre mencione que investimentos têm risco
- Se o usuário fornecer números reais (salário, dívidas, metas), use-os na resposta
- Organize respostas com tópicos quando houver múltiplos pontos
- Seja honesto quando algo estiver fora do escopo (ex: declaração de IR complexa)
- Você pode usar seu conhecimento geral sobre finanças mesmo sem o contexto do dataset
"""

    if context_block:
        system_prompt += f"\n{context_block}\nUse os exemplos acima apenas se forem relevantes para a pergunta.\n"

    ollama_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        ollama_messages.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant"):
        response_box = st.empty()
        full_response = ""
        try:
            stream = ollama.chat(
                model=model_name,
                messages=ollama_messages,
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                full_response += token
                response_box.markdown(full_response + "▌")
            response_box.markdown(full_response)
        except Exception as e:
            full_response = (
                f"❌ **Erro ao conectar ao Ollama.**\n\n"
                f"Verifique se o Ollama está rodando com `ollama serve`.\n\n"
                f"Detalhe: `{e}`"
            )
            response_box.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})\
        
def process_file(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file.type == "text/csv":
        df = pd.read_csv(file)
        return df.to_string() # Converte a tabela em texto
    elif "spreadsheetml" in file.type: # Excel
        df = pd.read_excel(file)
        return df.to_string()
    return ""