import streamlit as st
import google.generativeai as genai
import pypdf
import json
import uuid
import sqlite3
import random
import os
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
    page_icon="🐱",
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
    
def deletar_estudo_bd(id_estudo):
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    c.execute("DELETE FROM estudos WHERE id=?", (id_estudo,))
    conn.commit()
    conn.close()

init_db()

# --- 4. CATÁLOGO DE VENDAS (MAPEADO) ---
CATALOGO_PREMIUM = {
    "direito": {
        "visual": {"badge": "🔥 OFERTA JURÍDICA", "titulo": "KIT OAB 2026", "subtitulo": "Vade Mecum e Doutrinas", "icone": "⚖️", "bg_style": "background: linear-gradient(135deg, #240b36 0%, #c31432 100%);", "btn_text": "VER PREÇO NA AMAZON"},
        "produtos": [
            {"nome": "Vade Mecum Saraiva 2026", "link": "https://amzn.to/4qJymYt"},
            {"nome": "Vade Mecum Rideel Compacto", "link": "https://amzn.to/4qAOVWf"},
            {"nome": "CLT Organizada - LTr", "link": "https://amzn.to/45jNwuK"},
            {"nome": "Manual Direito Civil", "link": "https://amzn.to/4sKGLft"}
        ]
    },
    "tecnologia": {
        "visual": {"badge": "⚡ SETUP PRO", "titulo": "NOTEBOOKS & GAMER", "subtitulo": "Potência para programar.", "icone": "💻", "bg_style": "background: linear-gradient(135deg, #000428 0%, #004e92 100%);", "btn_text": "CONFIRMAR OFERTA"},
        "produtos": [
            {"nome": "Notebook Acer Aspire 5", "link": "https://amzn.to/4pJLkUC"},
            {"nome": "Mouse Logitech MX Master", "link": "https://amzn.to/3LyNpVu"},
            {"nome": "Teclado Mecânico Keychron", "link": "https://amzn.to/49BErP3"},
            {"nome": "Monitor Dell IPS 24", "link": "https://amzn.to/4pFde4d"}
        ]
    },
    "policial": {
        "visual": {"badge": "🛡️ OPERACIONAL", "titulo": "KIT APROVAÇÃO POLÍCIA", "subtitulo": "Apostilas e Tático.", "icone": "🚓", "bg_style": "background: linear-gradient(135deg, #16222A 0%, #3A6073 100%);", "btn_text": "VER EQUIPAMENTOS"},
        "produtos": [
            {"nome": "Apostila Alfacon Policial", "link": "https://amzn.to/4qPWLeq"},
            {"nome": "Vade Mecum Carreiras Policiais", "link": "https://amzn.to/4jK4vMs"},
            {"nome": "Coturno Tático Militar", "link": "https://amzn.to/4qXVCBy"}
        ]
    },
    "geral": {
        "visual": {"badge": "🎁 IMPERDÍVEL", "titulo": "KINDLE & FOCO", "subtitulo": "O essencial do estudante.", "icone": "🎒", "bg_style": "background: linear-gradient(135deg, #1A2980 0%, #26D0CE 100%);", "btn_text": "APROVEITAR AGORA"},
        "produtos": [
            {"nome": "Kindle 11ª Geração", "link": "https://amzn.to/3NpLfYP"},
            {"nome": "Fone JBL Cancelamento Ruído", "link": "https://amzn.to/49Z1vsr"},
            {"nome": "Garrafa Térmica", "link": "https://amzn.to/4sL9elk"},
            {"nome": "Mochila Antifurto", "link": "https://amzn.to/4sKkRZD"}
        ]
    }
}

def ia_escolher_categoria(contexto_usuario):
    if not contexto_usuario or len(contexto_usuario) < 5: return random.choice(["geral", "tecnologia"])
    if API_KEY:
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            resp = model.generate_content(f"Classifique: '{contexto_usuario[:500]}' em: direito, tecnologia, policial, geral. Só a palavra.").text.strip().lower()
            if "direito" in resp: return "direito"
            if "tecnolo" in resp: return "tecnologia"
            if "policia" in resp: return "policial"
        except: pass
    ctx = contexto_usuario.lower()
    if any(x in ctx for x in ["lei", "juridico"]): return "direito"
    if any(x in ctx for x in ["python", "code"]): return "tecnologia"
    if any(x in ctx for x in ["policia", "taf"]): return "policial"
    return "geral"

# --- 5. CSS (VISUAL REFINADO & RESPONSIVO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700;900&display=swap');
    
    /* RESET GERAL */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #090909; }
    .stApp { background-color: #090909; }
    section[data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #222; }
    
    /* FORÇAR QUADRADO EM TUDO */
    .stButton button, img, .super-banner, .lib-card, input, .pix-container, .questao-container, div[data-baseweb="tab"] {
        border-radius: 0px !important;
    }

    /* --- ABAS À ESQUERDA (FIXED) --- */
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: #111; padding: 0; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px;
        background-color: transparent; 
        color: #888; 
        border: none;
        border-right: 1px solid #333;
        border-bottom: 1px solid #333;
        flex-grow: 1;
        
        /* O PULO DO GATO PARA ALINHAR À ESQUERDA */
        justify-content: flex-start !important; 
        text-align: left !important;
        padding-left: 20px !important;
        font-weight: 500;
    }
    /* Texto dentro da aba */
    .stTabs [data-baseweb="tab"] > div {
        align-items: center; /* Centraliza verticalmente o texto */
    }
    
    .stTabs [aria-selected="true"] { 
        background-color: #222 !important; 
        color: #FFF !important; 
        border-top: 2px solid #F0C14B !important; 
        border-bottom: none !important;
    }

    /* --- SUPER BANNER PULSANTE --- */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(240, 193, 75, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(240, 193, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(240, 193, 75, 0); }
    }

    .super-banner {
        display: block; text-decoration: none; padding: 25px 20px; margin: 20px 0;
        position: relative; overflow: hidden; 
        border: 1px solid rgba(255,255,255,0.1);
        animation: pulse-border 2s infinite; /* Chama atenção */
        transition: transform 0.2s;
    }
    .super-banner:hover { transform: scale(1.02); filter: brightness(1.1); }
    
    .sb-badge { 
        position: absolute; top: 0; right: 0; background: #FFD700; color: #000; 
        font-size: 0.6rem; font-weight: 900; padding: 4px 8px; text-transform: uppercase; 
    }
    .sb-icon { font-size: 3.5rem; margin-bottom: 15px; display: block; text-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .sb-title { color: #FFF; font-weight: 900; font-size: 1.3rem; line-height: 1; margin-bottom: 5px; display: block; text-transform: uppercase;}
    .sb-prod-name { 
        background: rgba(0,0,0,0.4); color: #FFF; font-size: 0.8rem; padding: 5px; 
        display: inline-block; margin-bottom: 15px; font-weight: bold; border-left: 3px solid #FFD700;
    }
    .sb-button { 
        background: #FFF; color: #000; text-align: center; font-weight: 900; padding: 12px; 
        display: block; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;
    }

    /* --- CARD BIBLIOTECA (Clean) --- */
    .lib-card {
        background: #111; border: 1px solid #333; padding: 20px; height: 100%;
        transition: 0.2s; cursor: pointer; text-align: left;
        border-left: 2px solid #333;
    }
    .lib-card:hover { background: #1a1a1a; border-left-color: #F0C14B; }
    .lib-title { font-weight: 700; color: #EEE; font-size: 1.1rem; margin-bottom: 8px; }
    .lib-info { color: #666; font-size: 0.8rem; display: flex; justify-content: space-between; }

    /* --- RESPONSIVIDADE MOBILE --- */
    @media only screen and (max-width: 600px) {
        h1 { font-size: 2.2rem !important; }
        .stButton button { padding: 15px !important; font-size: 1rem !important; }
        .lib-card { margin-bottom: 10px; }
        /* No mobile, as colunas viram linhas automaticamente */
        [data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important; }
        /* Banner ocupa largura total */
        .super-banner { margin: 10px 0; }
    }

    /* PIX */
    .pix-container { background: #111; border: 1px dashed #555; padding: 20px; text-align: center; margin-top: 20px;}
    .pix-key { font-family: monospace; background: #000; padding: 15px; color: #00FF7F; font-size: 1rem; word-break: break-all; border: 1px solid #333; }

    /* QUESTÕES */
    .questao-container { background-color: #111; border: 1px solid #333; border-left: 3px solid #444; padding: 25px; margin-bottom: 30px; }
    .feedback-correct { background: rgba(5, 50, 20, 0.5); border: 1px solid #0F5132; color: #75B798; padding: 15px; margin-top: 10px; font-weight: bold;}
    .feedback-wrong { background: rgba(50, 5, 10, 0.5); border: 1px solid #842029; color: #EA868F; padding: 15px; margin-top: 10px; font-weight: bold;}

</style>
""", unsafe_allow_html=True)

# --- 6. ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state: st.session_state.chat_ativo_id = None
if "mensagens_ia" not in st.session_state: st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA."}]

# --- 7. FUNÇÕES ---
def ler_pdf(arquivo):
    try:
        leitor = pypdf.PdfReader(arquivo)
        texto = ""
        for pagina in leitor.pages:
            res = pagina.extract_text()
            if res: texto += res + "\n"
        if len(texto.strip()) < 50: return None, "PDF ilegível."
        return texto, None
    except Exception as e: return None, str(e)

def chamar_ia_json(texto, tipo):
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = """Gere um JSON estrito. Estrutura: [{"id": 1, "pergunta": "...", "opcoes": ["A) ...", "B) ..."], "correta": "A", "comentario": "..."}]"""
    if len(texto) < 500: contexto = f"Assunto: {texto}"
    else: contexto = f"Modo: {tipo}. Texto: {texto[:30000]}"
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
    st.session_state.pagina_atual = "biblioteca" 
    st.rerun()

# --- 8. BARRA LATERAL (NAVEGAÇÃO + SUPER ADS) ---
with st.sidebar:
    st.markdown("<h1 style='color: white; font-family: Inter; font-weight: 900; letter-spacing: -2px; margin:0;'>PRATICA<span style='color:#F0C14B'>.AI</span></h1>", unsafe_allow_html=True)
    st.caption("Versão 4.0 - Mobile Ready")
    st.markdown("---")
    
    # Navegação com ícones grandes
    if st.button("📄 NOVO UPLOAD", use_container_width=True): st.session_state.pagina_atual = "upload"; st.rerun()
    if st.button("📚 BIBLIOTECA", use_container_width=True): st.session_state.pagina_atual = "biblioteca"; st.rerun()
    if st.button("🤖 TUTOR IA", use_container_width=True): st.session_state.pagina_atual = "chat_ia"; st.rerun()
    if st.button("🐱 APOIE (PIX)", use_container_width=True): st.session_state.pagina_atual = "apoio"; st.rerun()
    
    st.markdown("---")
    
    # === SUPER BANNER DE VENDAS INTELIGENTE ===
    contexto_usuario = ""
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo: contexto_usuario = estudo_ativo['titulo']
    elif len(st.session_state.mensagens_ia) > 1:
        contexto_usuario = st.session_state.mensagens_ia[-2]['content']

    cat_nome = ia_escolher_categoria(contexto_usuario)
    cat_data = CATALOGO_PREMIUM[cat_nome]
    
    # Sorteia um produto específico para mostrar o nome real
    prod_escolhido = random.choice(cat_data["produtos"])
    visual = cat_data["visual"]

    st.markdown("<p style='font-size: 0.7rem; color: #666; font-weight: 800; letter-spacing: 1px; margin-bottom: 5px;'>PATROCINADO</p>", unsafe_allow_html=True)
    
    # Card HTML Puro com Animação
    st.markdown(f"""
    <a href="{prod_escolhido['link']}" target="_blank" class="super-banner" style="{visual['bg_style']}">
        <div class="sb-badge">{visual['badge']}</div>
        <span class="sb-icon">{visual['icone']}</span>
        <span class="sb-title">{visual['titulo']}</span>
        <div class="sb-prod-name">👉 {prod_escolhido['nome']}</div>
        <span class="sb-button" style="color: black;">{visual['btn_text']}</span>
    </a>
    """, unsafe_allow_html=True)

# --- 9. ÁREA PRINCIPAL ---

# >>> UPLOAD (Minimalista) <<<
if st.session_state.pagina_atual == "upload":
    st.markdown("""
    <div style="text-align: left; margin-top: 40px; margin-bottom: 40px;">
        <h1 style="font-size: 3rem; color: #FFF; font-weight: 900; line-height: 1.1;">ESTUDE MENOS,<br><span style="color: #444;">APRENDA MAIS.</span></h1>
        <p style="color: #888; font-size: 1.1rem; margin-top: 10px;">Suba seu PDF e deixe a IA criar sua prova.</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        arquivo = st.file_uploader("SELECIONE O ARQUIVO (PDF)", type="pdf")
    with c2:
        modo = st.radio("OBJETIVO:", ["Criar Questões", "Extrair Prova"])
        if arquivo and st.button("INICIAR PROCESSAMENTO ->", type="primary", use_container_width=True):
            with st.spinner("ANALISANDO..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes)
                    else: st.error("Erro ao processar.")

# >>> BIBLIOTECA (COM ABAS ALINHADAS) <<<
elif st.session_state.pagina_atual == "biblioteca":
    
    abas_titulos = ["📂 Meus Arquivos"]
    estudo_ativo = None
    
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo:
            abas_titulos.append(f"📝 {estudo_ativo['titulo']}")
            
    abas = st.tabs(abas_titulos)
    
    # ABA 1: LISTA
    with abas[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.historico:
            st.info("Sua biblioteca está vazia. Faça um upload!")
        else:
            cols = st.columns(3)
            for i, estudo in enumerate(st.session_state.historico):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="lib-card">
                        <div class="lib-title">{estudo['titulo']}</div>
                        <div class="lib-info">
                            <span>{estudo['data']}</span>
                            <span>{len(estudo['questoes'])} questões</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_act1, c_act2 = st.columns([3, 1])
                    with c_act1:
                        if st.button("ABRIR ESTUDO", key=f"open_{estudo['id']}", use_container_width=True):
                            st.session_state.chat_ativo_id = estudo['id']; st.rerun()
                    with c_act2:
                        if st.button("✕", key=f"del_{estudo['id']}", use_container_width=True):
                            deletar_estudo_bd(estudo['id'])
                            if st.session_state.chat_ativo_id == estudo['id']: st.session_state.chat_ativo_id = None
                            st.session_state.historico = carregar_historico_bd(); st.rerun()

    # ABA 2: PROVA ATIVA
    if estudo_ativo and len(abas) > 1:
        with abas[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            c_h1, c_h2 = st.columns([6, 2])
            with c_h1: st.title(estudo_ativo['titulo'])
            with c_h2: 
                if st.button("FECHAR X", use_container_width=True):
                    st.session_state.chat_ativo_id = None; st.rerun()
                
            st.markdown("---")
            for index, q in enumerate(estudo_ativo['questoes']):
                st.markdown(f"""
                <div class="questao-container">
                    <div style="color: #666; font-size: 0.8rem; margin-bottom: 10px; font-weight:bold;">QUESTÃO {index + 1:02d}</div>
                    <div class="questao-texto">{q['pergunta']}</div>
                </div>""", unsafe_allow_html=True)
                
                res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
                idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
                escolha = st.radio("Sua resposta:", q['opcoes'], index=idx, key=f"q_{estudo_ativo['id']}_{q['id']}", label_visibility="collapsed")
                
                if escolha and escolha != res_salva:
                    estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                    salvar_estudo_bd(estudo_ativo); st.rerun()
                
                if res_salva:
                    letra_user = res_salva.split(")")[0].strip().upper()
                    letra_correta = q['correta'].strip().upper()
                    if letra_user == letra_correta: st.markdown(f"""<div class="feedback-correct">✓ RESPOSTA CORRETA<br><span style="font-weight:normal">{q['comentario']}</span></div>""", unsafe_allow_html=True)
                    else: st.markdown(f"""<div class="feedback-wrong">✕ INCORRETO (Era {letra_correta})<br><span style="font-weight:normal">{q['comentario']}</span></div>""", unsafe_allow_html=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
            
            if st.button("REFAZER SIMULADO ↺", use_container_width=True):
                estudo_ativo["respostas_usuario"] = {}
                salvar_estudo_bd(estudo_ativo); st.rerun()

# >>> TUTOR IA <<<
elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA")
    modo_tutor = st.radio("OPÇÕES:", ["💬 Conversar", "📝 Gerar Simulado"], horizontal=True)
    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
    if modo_tutor == "💬 Conversar":
        for msg in st.session_state.mensagens_ia:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role): st.markdown(msg["content"])
        if prompt := st.chat_input("Dúvida..."):
            st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    model = genai.GenerativeModel('gemini-flash-latest')
                    resp = model.generate_content(f"Seja didático. User: {prompt}").text
                    st.markdown(resp)
                    st.session_state.mensagens_ia.append({"role": "model", "content": resp})
    else:
        if assunto := st.chat_input("Gerar simulado sobre..."):
             with st.spinner(f"Criando: {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                if questoes: criar_novo_estudo(f"Simulado: {assunto}", questoes)

# >>> APOIO (GATOS) <<<
elif st.session_state.pagina_atual == "apoio":
    st.title("🐱 APOIE NOSSO PROJETO!!")
    st.markdown("<h3 style='color: #888;'>Ajude a manter o servidor ligado!</h3>", unsafe_allow_html=True)
    
    # LAYOUT PIRÂMIDE
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("static/gato1.jpeg"): st.image("static/gato1.jpeg", caption="Exausta após corrigir bugs no servidor.", use_container_width=True)
        elif os.path.exists("gato1.jpeg"): st.image("gato1.jpeg", caption="Exausta após corrigir bugs no servidor.", use_container_width=True)
    
    c_base1, c_base2 = st.columns(2)
    with c_base1:
        if os.path.exists("static/gato2.jpeg"): st.image("static/gato2.jpeg", caption="A Gerente de TI analisando se você estudou hoje.", use_container_width=True)
        elif os.path.exists("gato2.jpeg"): st.image("gato2.jpeg", caption="A Gerente de TI analisando se você estudou hoje.", use_container_width=True)
    with c_base2:
        if os.path.exists("static/gato3.jpeg"): st.image("static/gato3.jpeg", caption="Esperando o Pix cair pra comprar sachê premium.", use_container_width=True)
        elif os.path.exists("gato3.jpeg"): st.image("gato3.jpeg", caption="Esperando o Pix cair pra comprar sachê premium.", use_container_width=True)

    st.markdown("<br><div class='pix-container'><p style='color:#AAA; margin-bottom:10px;'>Copie a chave aleatória:</p><div class='pix-key'>5b84b80d-c11a-4129-b897-74fb6371dfce</div></div>", unsafe_allow_html=True)