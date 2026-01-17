import streamlit as st
import google.generativeai as genai
import pypdf
import json
import uuid
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE SEGURANÇA (HÍBRIDA) ---
# Tenta pegar dos segredos do servidor. Se não der, usa a fixa (fallback).
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Chave de fallback para rodar localmente no seu PC
    API_KEY = "AIzaSyAq0c34TLlblT-a6ysdDr07edPBfnqR4kA"

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. SETUP DA PÁGINA ---
st.set_page_config(
    page_title="Pratica.ai",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. CSS "PRATICA.AI" (VISUAL DARK & SQUARE) ---
st.markdown("""
<style>
    /* FONTE E GERAL */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #000000;
    }
    
    .stApp { background-color: #000000; }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #0A0A0A;
        border-right: 1px solid #333;
    }
    
    /* Botões da Sidebar */
    .stButton button {
        text-align: left;
        padding: 10px;
        border: 1px solid transparent;
        background: transparent;
        color: #888;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        width: 100%;
        border-radius: 0px !important;
    }
    .stButton button:hover {
        color: #FFF; 
        background: #1A1A1A;
        border: 1px solid #333;
    }
    
    /* Botão Pequeno (Lápis) */
    .small-btn button {
        padding: 5px !important;
        text-align: center;
        font-size: 1.2rem !important;
    }

    /* --- CARDS DE QUESTÕES --- */
    .questao-container {
        background-color: #111111;
        border: 1px solid #333;
        border-left: 4px solid #333;
        padding: 30px;
        margin-bottom: 40px;
        border-radius: 0px;
    }
    
    .questao-header {
        font-family: 'JetBrains Mono', monospace;
        color: #666;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 15px;
    }
    
    .questao-texto {
        font-size: 1.2rem;
        line-height: 1.6;
        color: #FFF;
        font-weight: 400;
        margin-bottom: 25px;
    }

    /* --- FEEDBACK VISUAL --- */
    .feedback-box {
        margin-top: 20px;
        padding: 20px;
        border-radius: 0px;
        font-size: 0.95rem;
        animation: fadeIn 0.5s;
    }
    .feedback-correct {
        background-color: #051B11;
        border: 1px solid #0F5132;
        border-left: 4px solid #198754;
        color: #75B798;
    }
    .feedback-wrong {
        background-color: #2C0B0E;
        border: 1px solid #842029;
        border-left: 4px solid #DC3545;
        color: #EA868F;
    }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    
    /* Inputs e Radios */
    input[type="text"] {
        background-color: #111 !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 0px !important;
    }
    .stRadio label { color: #CCC !important; font-size: 1rem; }
    
    /* Chat Tutor */
    .stChatMessage { background-color: #111; border: 1px solid #333; }

</style>
""", unsafe_allow_html=True)

# --- 4. GERENCIAMENTO DE ESTADO ---
if "historico" not in st.session_state:
    st.session_state.historico = [] 
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "upload" # upload, chat_ia, visualizacao
if "chat_ativo_id" not in st.session_state:
    st.session_state.chat_ativo_id = None
if "editando_id" not in st.session_state:
    st.session_state.editando_id = None
if "mensagens_ia" not in st.session_state:
    st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA. Posso criar simulados ou tirar dúvidas. Selecione o modo acima."}]

# --- 5. FUNÇÕES DO SISTEMA ---

def ler_pdf(arquivo):
    try:
        leitor = pypdf.PdfReader(arquivo)
        texto = ""
        for pagina in leitor.pages:
            res = pagina.extract_text()
            if res: texto += res + "\n"
        if len(texto.strip()) < 50: return None, "PDF ilegível (Imagem). Tente converter para texto primeiro."
        return texto, None
    except Exception as e: return None, str(e)

def chamar_ia_json(texto, tipo):
    """Gera JSON para simulado interativo"""
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = """Gere um JSON estrito. Estrutura: [{"id": 1, "pergunta": "...", "opcoes": ["A) ...", "B) ..."], "correta": "A", "comentario": "..."}]"""
    
    # Adapta o contexto dependendo se é texto puro (assunto) ou PDF
    if len(texto) < 500: # Provavelmente é só um assunto digitado no chat
        contexto = f"Crie um simulado de concurso nível difícil sobre o Assunto: {texto}"
    else:
        contexto = f"Modo: {tipo}. Baseado no Texto: {texto[:30000]}"
        
    try:
        response = model.generate_content(prompt + "\n\n" + contexto)
        limpo = response.text.replace("```json", "").replace("```", "").strip()
        if "[" in limpo: limpo = limpo[limpo.find("["):limpo.rfind("]")+1]
        return json.loads(limpo)
    except: return None

def criar_novo_estudo(nome_arquivo, questoes):
    novo_id = str(uuid.uuid4())
    novo_estudo = {
        "id": novo_id,
        "titulo": nome_arquivo,
        "data": datetime.now().strftime("%d/%m"),
        "questoes": questoes,
        "respostas_usuario": {} 
    }
    st.session_state.historico.insert(0, novo_estudo) 
    st.session_state.chat_ativo_id = novo_id
    st.session_state.pagina_atual = "visualizacao"

def reiniciar_prova(estudo):
    estudo["respostas_usuario"] = {}
    st.rerun()

# --- 6. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: JetBrains Mono;'>Pratica.ai_</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navegação Principal
    if st.button("＋ NOVO UPLOAD", use_container_width=True):
        st.session_state.pagina_atual = "upload"
        st.session_state.chat_ativo_id = None
        st.rerun()
        
    if st.button("🤖 TUTOR IA", use_container_width=True):
        st.session_state.pagina_atual = "chat_ia"
        st.session_state.chat_ativo_id = None
        st.rerun()
    
    st.markdown("<br><p style='font-size: 0.8rem; color: #666; text-transform: uppercase;'>Biblioteca</p>", unsafe_allow_html=True)
    
    # Lista de Estudos com Edição
    for estudo in st.session_state.historico:
        
        # Se estiver editando ESTE item (renomear)
        if st.session_state.editando_id == estudo["id"]:
            def salvar_nome():
                st.session_state.editando_id = None
            
            # Input direto na sidebar
            novo_nome = st.text_input("Novo nome:", value=estudo["titulo"], key=f"input_{estudo['id']}", on_change=salvar_nome)
            estudo["titulo"] = novo_nome 
            if st.button("Salvar", key=f"save_{estudo['id']}"):
                st.session_state.editando_id = None
                st.rerun()
                
        else:
            # Layout Normal: Botão Nome + Botão Lápis
            col_nav, col_edit = st.columns([5, 1])
            
            with col_nav:
                # Ícone visual para saber qual está ativo
                icone = "■" if st.session_state.chat_ativo_id == estudo["id"] else "□"
                if st.button(f"{icone} {estudo['titulo']}", key=f"btn_{estudo['id']}", use_container_width=True):
                    st.session_state.chat_ativo_id = estudo["id"]
                    st.session_state.pagina_atual = "visualizacao"
                    st.rerun()
            
            with col_edit:
                # Botão Lápis
                st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                if st.button("✎", key=f"edit_{estudo['id']}"):
                    st.session_state.editando_id = estudo["id"]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- 7. ÁREA PRINCIPAL ---

# PÁGINA 1: UPLOAD (HOME)
if st.session_state.pagina_atual == "upload":
    st.markdown("""
    <div style="text-align: left; margin-top: 80px;">
        <h1 style="font-size: 4rem; color: #FFF; line-height: 1;">PRATICA<br><span style="color: #444;">.AI</span></h1>
        <p style="color: #888; font-family: 'JetBrains Mono'; margin-top: 20px;">SISTEMA DE ESTUDOS INTELIGENTE</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_up, _ = st.columns([1, 1])
    with col_up:
        st.markdown("<br>", unsafe_allow_html=True)
        modo = st.radio("MODO DE OPERAÇÃO:", ["Criar Questões do PDF", "Extrair Prova do PDF"])
        st.markdown("<br>", unsafe_allow_html=True)
        arquivo = st.file_uploader("ARRASTE SEU PDF AQUI", type="pdf")
        
        if arquivo and st.button("PROCESSAR ARQUIVO ->", type="primary"):
            with st.spinner("ANALISANDO DADOS..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes); st.rerun()
                    else: st.error("Erro ao gerar questões. Verifique se o PDF tem texto legível.")

# PÁGINA 2: TUTOR IA (CHAT & GERADOR)
elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA")
    
    # Seletor de Modo do Tutor
    modo_tutor = st.radio("O QUE VOCÊ DESEJA?", ["💬 Chat / Texto", "📝 Gerar Simulado Interativo"], horizontal=True)
    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
    
    if modo_tutor == "💬 Chat / Texto":
        # MODO 1: CHAT NORMAL
        for msg in st.session_state.mensagens_ia:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(msg["content"])
                
        if prompt := st.chat_input("Ex: Me explique a diferença entre Dolo e Culpa..."):
            st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Digitando..."):
                    model = genai.GenerativeModel('gemini-flash-latest')
                    response = model.generate_content(f"Você é um tutor de concursos didático e direto. Usuário: {prompt}")
                    st.markdown(response.text)
                    st.session_state.mensagens_ia.append({"role": "model", "content": response.text})
                    
    else:
        # MODO 2: GERADOR DE SIMULADO
        st.info("Digite um assunto abaixo (ex: Crase, Python, Direito Penal) e a IA criará uma prova interativa completa na sua biblioteca.")
        
        if assunto := st.chat_input("Digite o assunto para o simulado..."):
            with st.spinner(f"Criando prova sobre: {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                
                if questoes:
                    titulo_simulado = f"Simulado: {assunto}"
                    criar_novo_estudo(titulo_simulado, questoes)
                    st.success("Simulado Criado! Redirecionando...")
                    st.rerun()
                else:
                    st.error("A IA não conseguiu criar questões sobre esse assunto.")


# PÁGINA 3: VISUALIZAÇÃO DO ESTUDO (SIMULADO)
elif st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
    
    # Encontra o estudo atual
    estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
    
    if estudo_ativo:
        # Cabeçalho com Botão Reiniciar
        c1, c2 = st.columns([5, 1])
        with c1:
            st.title(estudo_ativo['titulo'])
        with c2:
            if st.button("↺ REINICIAR", use_container_width=True):
                reiniciar_prova(estudo_ativo)

        st.markdown("<div style='height: 1px; background-color: #333; margin-bottom: 40px;'></div>", unsafe_allow_html=True)

        # Loop de Questões
        for index, q in enumerate(estudo_ativo['questoes']):
            st.markdown(f"""
            <div class="questao-container">
                <div class="questao-header">QUESTÃO {index + 1:02d}</div>
                <div class="questao-texto">{q['pergunta']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Lógica de resposta
            res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
            # Descobre o índice da resposta salva para marcar a bolinha certa
            idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
            
            # O Radio Button que faz a mágica
            escolha = st.radio(
                "Alternativas:", 
                q['opcoes'], 
                index=idx, 
                key=f"r_{estudo_ativo['id']}_{q['id']}", 
                label_visibility="collapsed"
            )

            # Feedback Imediato
            if escolha:
                estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                letra_user = escolha.split(")")[0].strip().upper()
                letra_correta = q['correta'].strip().upper()
                
                if letra_user == letra_correta:
                    st.markdown(f"""<div class="feedback-box feedback-correct"><b>✓ CORRETO</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="feedback-box feedback-wrong"><b>✕ ERRADO (A correta é {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)