import streamlit as st
import google.generativeai as genai
import pypdf
import json
import uuid
import sqlite3
import random
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE SEGURANÇA ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
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

# --- 3. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS estudos
                 (id TEXT PRIMARY KEY, titulo TEXT, data TEXT, questoes TEXT, respostas TEXT)''')
    conn.commit()
    conn.close()

def carregar_historico_bd():
    try:
        conn = sqlite3.connect('dados_pratica.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM estudos ORDER BY data DESC")
        rows = c.fetchall()
        lista = []
        for row in rows:
            lista.append({
                "id": row["id"], "titulo": row["titulo"], "data": row["data"],
                "questoes": json.loads(row["questoes"]), "respostas_usuario": json.loads(row["respostas"])
            })
        conn.close()
        return lista
    except: return []

def salvar_estudo_bd(estudo):
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO estudos VALUES (?, ?, ?, ?, ?)''', 
                 (estudo["id"], estudo["titulo"], estudo["data"], 
                  json.dumps(estudo["questoes"]), json.dumps(estudo["respostas_usuario"])))
    conn.commit()
    conn.close()

init_db()

# --- 4. CATALOGO DE PRODUTOS "PREMIUM" ---
# Aqui configuramos o visual de cada categoria
CATALOGO_VISUAL = {
    "direito": {
        "icone": "⚖️",
        "titulo": "Vade Mecum 2026",
        "subtitulo": "Obrigatório para OAB",
        "badge": "MAIS VENDIDO",
        "cor_badge": "#FFD700", # Dourado
        "links": ["https://amzn.to/4qJymYt", "https://amzn.to/4qAOVWf", "https://amzn.to/45jNwuK", "https://amzn.to/4sKGLft"]
    },
    "tecnologia": {
        "icone": "💻",
        "titulo": "Setup de Estudos",
        "subtitulo": "Notebooks & Acessórios",
        "badge": "OFERTA RELÂMPAGO",
        "cor_badge": "#00FF7F", # Verde Neon
        "links": ["https://amzn.to/4pJLkUC", "https://amzn.to/3LyNpVu", "https://amzn.to/49BErP3", "https://amzn.to/4pFde4d"]
    },
    "policial": {
        "icone": "🛡️",
        "titulo": "Kit Policial",
        "subtitulo": "Apostilas & Tático",
        "badge": "APROVAÇÃO",
        "cor_badge": "#FF4500", # Laranja Forte
        "links": ["https://amzn.to/4qPWLeq", "https://amzn.to/4jK4vMs", "https://amzn.to/4qXVCBy", "https://amzn.to/4jOjNjx"]
    },
    "geral": {
        "icone": "🎒",
        "titulo": "Essenciais",
        "subtitulo": "Kindle, Fones e +",
        "badge": "PROMOÇÃO",
        "cor_badge": "#1E90FF", # Azul
        "links": ["https://amzn.to/3NpLfYP", "https://amzn.to/49Z1vsr", "https://amzn.to/4sL9elk", "https://amzn.to/4sKkRZD"]
    }
}

def ia_escolher_anuncio(contexto_usuario):
    """Define a categoria baseada no contexto"""
    if not contexto_usuario or len(contexto_usuario) < 5:
        return CATALOGO_VISUAL["geral"]

    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    Contexto: "{contexto_usuario[:500]}"
    Categorias: direito, tecnologia, policial, geral.
    Responda APENAS a categoria.
    """
    try:
        resp = model.generate_content(prompt).text.lower()
        if "direito" in resp: return CATALOGO_VISUAL["direito"]
        if "tec" in resp: return CATALOGO_VISUAL["tecnologia"]
        if "poli" in resp: return CATALOGO_VISUAL["policial"]
        return CATALOGO_VISUAL["geral"]
    except: return CATALOGO_VISUAL["geral"]

# --- 5. CSS REVOLUCIONÁRIO (VISUAL DE VENDAS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #050505; }
    .stApp { background-color: #050505; }
    section[data-testid="stSidebar"] { background-color: #0F0F0F; border-right: 1px solid #222; }
    
    /* --- CARD DE PRODUTO AMAZON STYLE --- */
    .product-card {
        background: #141414;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 0;
        margin: 20px 0;
        text-decoration: none;
        display: block;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border-color: #555;
    }
    
    .card-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background: #FFD700;
        color: #000;
        font-size: 0.6rem;
        font-weight: 900;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        z-index: 2;
    }
    
    .card-image-area {
        height: 100px;
        background: radial-gradient(circle, #2a2a2a 0%, #141414 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3.5rem;
    }
    
    .card-content {
        padding: 15px;
    }
    
    .card-title {
        color: #FFF;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 4px;
        display: block;
    }
    
    .card-subtitle {
        color: #888;
        font-size: 0.8rem;
        display: block;
        margin-bottom: 10px;
    }
    
    .card-rating {
        color: #FFB800;
        font-size: 0.8rem;
        letter-spacing: 2px;
        margin-bottom: 12px;
        display: block;
    }
    
    .card-btn {
        background: #F0C14B; /* Cor do botão Amazon */
        color: #111;
        text-align: center;
        font-weight: 700;
        padding: 10px;
        border-radius: 6px;
        display: block;
        font-size: 0.9rem;
        transition: 0.2s;
    }
    
    .card-btn:hover {
        background: #eebb30;
    }

    /* Outros Estilos do App */
    .stButton button {
        text-align: left; padding: 10px; border: 1px solid transparent;
        background: transparent; color: #888; width: 100%; border-radius: 6px !important;
    }
    .stButton button:hover { color: #FFF; background: #1A1A1A; border: 1px solid #333; }
    
    .questao-container {
        background-color: #111; border: 1px solid #333; border-left: 4px solid #333;
        padding: 30px; margin-bottom: 40px; border-radius: 0px;
    }
    .questao-texto { font-size: 1.2rem; line-height: 1.6; color: #FFF; margin-bottom: 25px; }
    .feedback-box { margin-top: 20px; padding: 20px; font-size: 0.95rem; }
    .feedback-correct { background-color: #051B11; border-left: 4px solid #198754; color: #75B798; }
    .feedback-wrong { background-color: #2C0B0E; border-left: 4px solid #DC3545; color: #EA868F; }
    
    input[type="text"], input[type="password"] { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. GERENCIAMENTO DE ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state: st.session_state.chat_ativo_id = None
if "editando_id" not in st.session_state: st.session_state.editando_id = None
if "mensagens_ia" not in st.session_state: st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA."}]

# --- 7. FUNÇÕES DE IA ---
def ler_pdf(arquivo):
    try:
        leitor = pypdf.PdfReader(arquivo)
        texto = ""
        for pagina in leitor.pages:
            res = pagina.extract_text()
            if res: texto += res + "\n"
        if len(texto.strip()) < 50: return None, "PDF ilegível (Imagem)."
        return texto, None
    except Exception as e: return None, str(e)

def chamar_ia_json(texto, tipo):
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = """Gere um JSON estrito. Estrutura: [{"id": 1, "pergunta": "...", "opcoes": ["A) ...", "B) ..."], "correta": "A", "comentario": "..."}]"""
    if len(texto) < 500: contexto = f"Crie um simulado de concurso nível difícil sobre o Assunto: {texto}"
    else: contexto = f"Modo: {tipo}. Baseado no Texto: {texto[:30000]}"
    try:
        response = model.generate_content(prompt + "\n\n" + contexto)
        limpo = response.text.replace("```json", "").replace("```", "").strip()
        if "[" in limpo: limpo = limpo[limpo.find("["):limpo.rfind("]")+1]
        return json.loads(limpo)
    except: return None

def criar_novo_estudo(nome_arquivo, questoes):
    novo_id = str(uuid.uuid4())
    novo_estudo = {
        "id": novo_id, "titulo": nome_arquivo, "data": datetime.now().strftime("%d/%m"),
        "questoes": questoes, "respostas_usuario": {} 
    }
    salvar_estudo_bd(novo_estudo)
    st.session_state.historico = carregar_historico_bd()
    st.session_state.chat_ativo_id = novo_id
    st.session_state.pagina_atual = "visualizacao"

# --- 8. BARRA LATERAL (COM CARD PREMIUM) ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: Inter; font-weight: 900; letter-spacing: -1px;'>Pratica.ai <span style='color:#F0C14B'>.</span></h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("＋ NOVO UPLOAD", use_container_width=True):
        st.session_state.pagina_atual = "upload"
        st.session_state.chat_ativo_id = None
        st.rerun()
        
    if st.button("🤖 TUTOR IA", use_container_width=True):
        st.session_state.pagina_atual = "chat_ia"
        st.session_state.chat_ativo_id = None
        st.rerun()
    
    st.markdown("<br><p style='font-size: 0.7rem; color: #666; text-transform: uppercase; font-weight: bold;'>Sua Biblioteca</p>", unsafe_allow_html=True)
    
    for estudo in st.session_state.historico:
        if st.session_state.editando_id == estudo["id"]:
            def salvar_nome(): st.session_state.editando_id = None
            novo_nome = st.text_input("Nome:", value=estudo["titulo"], key=f"input_{estudo['id']}", on_change=salvar_nome)
            estudo["titulo"] = novo_nome 
            if st.button("Salvar", key=f"save_{estudo['id']}"):
                salvar_estudo_bd(estudo)
                st.session_state.editando_id = None
                st.rerun()
        else:
            col_nav, col_edit = st.columns([5, 1])
            with col_nav:
                icone = "📂" if st.session_state.chat_ativo_id == estudo["id"] else "📁"
                if st.button(f"{icone} {estudo['titulo']}", key=f"btn_{estudo['id']}", use_container_width=True):
                    st.session_state.chat_ativo_id = estudo["id"]
                    st.session_state.pagina_atual = "visualizacao"
                    st.rerun()
            with col_edit:
                if st.button("✎", key=f"edit_{estudo['id']}"):
                    st.session_state.editando_id = estudo["id"]
                    st.rerun()

    # --- CARD DE ANÚNCIO PREMIUM (IA POWERED) ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Detectar Contexto
    contexto_usuario = ""
    if st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo: contexto_usuario = estudo_ativo['titulo']
    elif st.session_state.pagina_atual == "chat_ia":
        if len(st.session_state.mensagens_ia) > 1:
             contexto_usuario = st.session_state.mensagens_ia[-2]['content'] # Pega ultima msg user

    # 2. IA Escolhe a Categoria
    produto_info = ia_escolher_anuncio(contexto_usuario)
    link_final = random.choice(produto_info["links"]) # Pega um link aleatório da lista daquela categoria

    # 3. Renderiza o Card Bonito
    st.markdown(f"""
    <a href="{link_final}" target="_blank" class="product-card">
        <div class="card-badge" style="background: {produto_info['cor_badge']}">{produto_info['badge']}</div>
        <div class="card-image-area">
            {produto_info['icone']}
        </div>
        <div class="card-content">
            <span class="card-title">{produto_info['titulo']}</span>
            <span class="card-subtitle">{produto_info['subtitulo']}</span>
            <span class="card-rating">⭐⭐⭐⭐⭐ (4.9)</span>
            <span class="card-btn">VER PREÇO E OFERTA</span>
        </div>
    </a>
    """, unsafe_allow_html=True)

    # 4. Doação Pix Discreta
    with st.expander("☕ Pagar um café pro Dev"):
        st.caption("Chave Pix:")
        st.code("5b84b80d-c11a-4129-b897-74fb6371dfce", language="text")

# --- 9. ÁREA PRINCIPAL ---
if st.session_state.pagina_atual == "upload":
    st.markdown("""
    <div style="text-align: left; margin-top: 80px;">
        <h1 style="font-size: 4rem; color: #FFF; line-height: 1; font-weight: 900; letter-spacing: -2px;">PRATICA<span style="color: #F0C14B;">.AI</span></h1>
        <p style="color: #888; margin-top: 20px; font-size: 1.2rem;">ESTUDE MENOS, APRENDA MAIS.</p>
    </div>
    """, unsafe_allow_html=True)
    col_up, _ = st.columns([1, 1])
    with col_up:
        st.markdown("<br>", unsafe_allow_html=True)
        modo = st.radio("O QUE VAMOS FAZER HOJE?", ["Criar Questões do PDF", "Extrair Prova do PDF"])
        st.markdown("<br>", unsafe_allow_html=True)
        arquivo = st.file_uploader("ARRASTE SEU ARQUIVO AQUI", type="pdf")
        if arquivo and st.button("PROCESSAR ARQUIVO ->", type="primary"):
            with st.spinner("LENDO ARQUIVO..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes); st.rerun()
                    else: st.error("Erro ao processar.")

elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA")
    st.caption("Acesso Gratuito e Ilimitado")
    
    modo_tutor = st.radio("OPÇÕES:", ["💬 Conversar", "📝 Criar Simulado"], horizontal=True)
    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
    
    if modo_tutor == "💬 Conversar":
        for msg in st.session_state.mensagens_ia:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role): st.markdown(msg["content"])
        if prompt := st.chat_input("Dúvida ou assunto..."):
            st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    model = genai.GenerativeModel('gemini-flash-latest')
                    response = model.generate_content(f"Seja didático e direto. Usuário: {prompt}")
                    st.markdown(response.text)
                    st.session_state.mensagens_ia.append({"role": "model", "content": response.text})
                    st.rerun()
    else:
        st.info("Digite um tema para gerar um simulado completo na hora.")
        if assunto := st.chat_input("Ex: Direito Constitucional, Python, SUS..."):
            with st.spinner(f"Criando prova sobre: {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                if questoes: criar_novo_estudo(f"Simulado: {assunto}", questoes); st.rerun()

elif st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
    estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
    if estudo_ativo:
        c1, c2 = st.columns([5, 1])
        with c1: st.title(estudo_ativo['titulo'])
        with c2:
            if st.button("↺ REINICIAR", use_container_width=True):
                estudo_ativo["respostas_usuario"] = {}
                salvar_estudo_bd(estudo_ativo); st.rerun()
        st.markdown("<div style='height: 1px; background-color: #333; margin-bottom: 40px;'></div>", unsafe_allow_html=True)
        for index, q in enumerate(estudo_ativo['questoes']):
            st.markdown(f"""
            <div class="questao-container">
                <div style="color: #666; font-size: 0.8rem; margin-bottom: 10px;">QUESTÃO {index + 1:02d}</div>
                <div class="questao-texto">{q['pergunta']}</div>
            </div>""", unsafe_allow_html=True)
            res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
            idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
            escolha = st.radio("Alternativas:", q['opcoes'], index=idx, key=f"r_{estudo_ativo['id']}_{q['id']}", label_visibility="collapsed")
            if escolha and escolha != res_salva:
                estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                salvar_estudo_bd(estudo_ativo); st.rerun()
            if res_salva:
                letra_user = res_salva.split(")")[0].strip().upper()
                letra_correta = q['correta'].strip().upper()
                if letra_user == letra_correta: st.markdown(f"""<div class="feedback-box feedback-correct"><b>✓ ACERTOU</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                else: st.markdown(f"""<div class="feedback-box feedback-wrong"><b>✕ ERROU (Correta: {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)