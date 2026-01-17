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

# --- 4. CATÁLOGO PREMIUM ---
CATALOGO_PREMIUM = {
    "direito": {
        "links": ["https://amzn.to/4qJymYt", "https://amzn.to/4qAOVWf", "https://amzn.to/45jNwuK", "https://amzn.to/4sKGLft"],
        "visual": {"badge": "🔥 OFERTA JURÍDICA", "titulo": "KIT VADE MECUM", "subtitulo": "Melhores materiais para OAB.", "icone": "⚖️", "bg_style": "background: linear-gradient(135deg, #4b148c 0%, #c7941d 100%);", "btn_color": "#FFD700", "btn_text": "#000"}
    },
    "tecnologia": {
        "links": ["https://amzn.to/4pJLkUC", "https://amzn.to/3LyNpVu", "https://amzn.to/49BErP3", "https://amzn.to/4pFde4d"],
        "visual": {"badge": "⚡ SETUP TECH", "titulo": "NOTEBOOKS PRO", "subtitulo": "Potência para programar.", "icone": "💻", "bg_style": "background: linear-gradient(135deg, #006cff 0%, #00ffc8 100%);", "btn_color": "#FFF", "btn_text": "#000"}
    },
    "policial": {
        "links": ["https://amzn.to/4qPWLeq", "https://amzn.to/4jK4vMs", "https://amzn.to/4qXVCBy"],
        "visual": {"badge": "🛡️ APROVAÇÃO", "titulo": "CARREIRAS POLICIAIS", "subtitulo": "Material tático focado.", "icone": "🚓", "bg_style": "background: linear-gradient(135deg, #ff4500 0%, #ff9100 100%);", "btn_color": "#FFF", "btn_text": "#FF4500"}
    },
    "geral": {
        "links": ["https://amzn.to/3NpLfYP", "https://amzn.to/49Z1vsr", "https://amzn.to/4sL9elk"],
        "visual": {"badge": "🎁 PROMOÇÃO", "titulo": "ESSENCIAIS", "subtitulo": "Kindle, Fones e mais.", "icone": "🎒", "bg_style": "background: linear-gradient(135deg, #ff00a8 0%, #8a2be2 100%);", "btn_color": "#FFF", "btn_text": "#8A2BE2"}
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

# --- 5. CSS (VISUAL DE VENDAS + GATOS + ABAS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #050505; }
    .stApp { background-color: #050505; }
    section[data-testid="stSidebar"] { background-color: #0F0F0F; border-right: 1px solid #222; }
    
    /* ABAS ESTILO GOOGLE */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111; border-radius: 8px 8px 0 0; padding: 10px 20px; color: #888; border: 1px solid #333; border-bottom: none;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #FFF; background-color: #222; }
    .stTabs [aria-selected="true"] {
        background-color: #050505 !important; color: #FFF !important; border-top: 2px solid #F0C14B !important; font-weight: bold;
    }

    /* CARD BIBLIOTECA */
    .lib-card {
        background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px;
        transition: 0.2s; cursor: pointer; text-align: left; height: 100%;
    }
    .lib-card:hover { border-color: #555; background: #161616; transform: translateY(-2px); }
    .lib-title { font-weight: 700; color: #FFF; font-size: 1rem; margin-bottom: 5px; }
    .lib-date { color: #666; font-size: 0.8rem; }
    .lib-icon { font-size: 1.5rem; float: right; opacity: 0.5; }

    /* SUPER BANNER */
    .super-banner {
        display: block; text-decoration: none; border-radius: 16px; padding: 20px; margin: 20px 0;
        position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: transform 0.3s ease; border: 2px solid rgba(255,255,255,0.1);
    }
    .super-banner:hover { transform: scale(1.03); }
    .sb-badge { position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,0.6); color: #FFF; font-size: 0.7rem; font-weight: 900; padding: 4px 10px; border-radius: 20px; }
    .sb-icon { font-size: 3.5rem; margin-bottom: 10px; display: block; }
    .sb-title { color: #FFF; font-weight: 900; font-size: 1.4rem; line-height: 1.1; margin-bottom: 8px; display: block; }
    .sb-subtitle { color: rgba(255,255,255,0.9); font-size: 0.9rem; display: block; margin-bottom: 20px; font-weight: 500; }
    .sb-button { background: #FFF; color: #000; text-align: center; font-weight: 800; padding: 12px 20px; border-radius: 50px; display: block; font-size: 1rem; text-transform: uppercase; }

    /* PIX & GATOS */
    .pix-container { background: #111; border: 1px dashed #444; border-radius: 15px; padding: 30px; text-align: center; }
    .pix-key { font-family: monospace; background: #222; padding: 15px; border-radius: 8px; color: #00FF7F; font-size: 1.1rem; margin: 20px 0; word-break: break-all; select-all; }
    img { border-radius: 12px; }
    
    /* QUESTÕES */
    .stButton button { text-align: left; background: transparent; color: #DDD; width: 100%; border-radius: 8px !important; }
    .stButton button:hover { background: #222; }
    .questao-container { background-color: #111; border: 1px solid #333; border-left: 4px solid #333; padding: 30px; margin-bottom: 40px; }
    .feedback-correct { background-color: #051B11; border-left: 4px solid #198754; color: #75B798; padding: 15px;}
    .feedback-wrong { background-color: #2C0B0E; border-left: 4px solid #DC3545; color: #EA868F; padding: 15px;}
    
    /* LOJA */
    .amazon-card { background: #FFF; border-radius: 8px; padding: 15px; text-align: center; display: block; text-decoration: none; border: 1px solid #DDD; }
    .amz-button { background: #FFD814; color: #000; padding: 8px; border-radius: 20px; display: block; margin-top: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 6. GERENCIAMENTO DE ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
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
    # Ao criar, vamos direto para a aba biblioteca (que vai detectar o ID ativo e abrir a prova)
    st.rerun()

# --- 8. BARRA LATERAL (SÓ ANÚNCIOS AGORA) ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: Inter; font-weight: 900; letter-spacing: -1px;'>Pratica.ai <span style='color:#F0C14B'>.</span></h2>", unsafe_allow_html=True)
    st.caption("Menu de navegação movido para o topo ↗")
    st.markdown("---")
    
    # Contexto para o Anúncio
    contexto_usuario = ""
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo: contexto_usuario = estudo_ativo['titulo']
    elif len(st.session_state.mensagens_ia) > 1:
        contexto_usuario = st.session_state.mensagens_ia[-2]['content']

    cat_nome = ia_escolher_categoria(contexto_usuario)
    cat_data = CATALOGO_PREMIUM[cat_nome]
    link_final = random.choice(cat_data["links"])
    visual = cat_data["visual"]

    st.markdown("<p style='font-size: 0.75rem; color: #888; font-weight: 800; letter-spacing: 1px; margin-bottom: 10px;'>OFERTA SUGERIDA</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <a href="{link_final}" target="_blank" class="super-banner" style="{visual['bg_style']}">
        <div class="sb-badge">{visual['badge']}</div>
        <span class="sb-icon">{visual['icone']}</span>
        <span class="sb-title">{visual['titulo']}</span>
        <span class="sb-subtitle">{visual['subtitulo']}</span>
        <span class="sb-button" style="background: {visual['btn_color']}; color: {visual['btn_text']};">VER OFERTA</span>
    </a>
    """, unsafe_allow_html=True)

# --- 9. NAVEGAÇÃO SUPERIOR (ABAS) ---

tab_inicio, tab_biblio, tab_tutor, tab_loja, tab_apoio = st.tabs(["☁️ Início", "📚 Biblioteca", "🤖 Tutor IA", "🛒 Loja", "🐱 Apoio"])

# >>> ABA 1: INÍCIO (UPLOAD) <<<
with tab_inicio:
    st.markdown("""
    <div style="text-align: center; margin: 50px 0;">
        <h1 style="font-size: 3.5rem; color: #FFF; font-weight: 900; letter-spacing: -2px;">PRATICA<span style="color: #444;">.AI</span></h1>
        <p style="color: #888; font-size: 1.2rem;">Transforme seus PDFs em simulados interativos em segundos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        modo = st.radio("O que vamos estudar?", ["Criar Questões Inéditas", "Extrair Prova Existente"], horizontal=True)
        arquivo = st.file_uploader("Arraste seu PDF aqui", type="pdf")
        if arquivo and st.button("🚀 Gerar Simulado", type="primary", use_container_width=True):
            with st.spinner("A IA está lendo seu material..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: 
                        criar_novo_estudo(arquivo.name, questoes) # Isso já dá rerun
                    else: st.error("Erro ao processar.")

# >>> ABA 2: BIBLIOTECA (SEUS ESTUDOS) <<<
with tab_biblio:
    # Se tem um chat ativo, mostra a PROVA
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo:
            b1, b2 = st.columns([6, 1])
            with b1: st.title(estudo_ativo['titulo'])
            with b2: 
                if st.button("⬅ VOLTAR"): 
                    st.session_state.chat_ativo_id = None
                    st.rerun()

            # Área da Prova
            for index, q in enumerate(estudo_ativo['questoes']):
                st.markdown(f"""
                <div class="questao-container">
                    <div style="color: #666; font-size: 0.8rem; margin-bottom: 10px;">QUESTÃO {index + 1:02d}</div>
                    <div class="questao-texto">{q['pergunta']}</div>
                </div>""", unsafe_allow_html=True)
                
                res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
                idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
                escolha = st.radio("Resposta:", q['opcoes'], index=idx, key=f"q_{estudo_ativo['id']}_{q['id']}", label_visibility="collapsed")
                
                if escolha and escolha != res_salva:
                    estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                    salvar_estudo_bd(estudo_ativo)
                    st.rerun()
                
                if res_salva:
                    letra_user = res_salva.split(")")[0].strip().upper()
                    letra_correta = q['correta'].strip().upper()
                    if letra_user == letra_correta: 
                        st.markdown(f"""<div class="feedback-correct"><b>✓ ACERTOU</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                    else: 
                        st.markdown(f"""<div class="feedback-wrong"><b>✕ ERROU (Correta: {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("↺ Reiniciar Simulado", use_container_width=True):
                estudo_ativo["respostas_usuario"] = {}
                salvar_estudo_bd(estudo_ativo); st.rerun()

    # Se NÃO tem chat ativo, mostra a GRADE DE CARDS
    else:
        st.title("📚 Minha Biblioteca")
        if not st.session_state.historico:
            st.info("Você ainda não tem estudos. Vá na aba 'Início' e suba um PDF!")
        else:
            # Grid de Estudos
            cols = st.columns(3)
            for i, estudo in enumerate(st.session_state.historico):
                with cols[i % 3]:
                    # Card Interativo (Gambiarra visual com Button)
                    # Usamos um botão invisível por cima ou apenas o botão nativo estilizado
                    st.markdown(f"""
                    <div class="lib-card">
                        <div class="lib-icon">📄</div>
                        <div class="lib-title">{estudo['titulo']}</div>
                        <div class="lib-date">Criado em: {estudo['data']}</div>
                        <div style="font-size: 0.8rem; color: #555; margin-top: 5px;">{len(estudo['questoes'])} questões</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_open, c_del = st.columns([4, 1])
                    with c_open:
                        if st.button("ABRIR", key=f"open_{estudo['id']}", use_container_width=True):
                            st.session_state.chat_ativo_id = estudo['id']
                            st.rerun()
                    with c_del:
                        if st.button("🗑️", key=f"del_{estudo['id']}", use_container_width=True):
                            deletar_estudo_bd(estudo['id'])
                            st.session_state.historico = carregar_historico_bd()
                            st.rerun()

# >>> ABA 3: TUTOR IA <<<
with tab_tutor:
    st.title("🤖 Tutor IA")
    modo_tutor = st.radio("", ["💬 Conversar", "📝 Gerar Simulado Rápido"], horizontal=True)
    
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
        assunto = st.text_input("Sobre qual assunto você quer treinar agora?")
        if assunto and st.button("Gerar Simulado Agora"):
             with st.spinner(f"Criando prova sobre {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                if questoes: criar_novo_estudo(f"Simulado: {assunto}", questoes)

# >>> ABA 4: LOJA <<<
with tab_loja:
    st.title("🛒 Loja Oficial")
    st.caption("Produtos selecionados com curadoria.")
    cat_tabs = st.tabs(CATALOGO_PREMIUM.keys())
    for aba, cat in zip(cat_tabs, CATALOGO_PREMIUM):
        with aba:
            links = CATALOGO_PREMIUM[cat]["links"]
            l_cols = st.columns(4)
            for i, link in enumerate(links):
                with l_cols[i % 4]:
                    st.markdown(f"""
                    <a href="{link}" target="_blank" class="amazon-card">
                        <span style="font-weight:bold; color:#333">Oferta #{i+1}</span>
                        <span class="amz-button">Ver na Amazon</span>
                    </a>
                    """, unsafe_allow_html=True)

# >>> ABA 5: APOIO <<<
with tab_apoio:
    st.title("🐱 Apoie o Projeto")
    # LAYOUT PIRÂMIDE
    c_top_left, c_top_center, c_top_right = st.columns([1, 2, 1])
    with c_top_center:
        if os.path.exists("static/gato1.jpeg"): # Ajuste o caminho se necessário
            st.image("static/gato1.jpeg", caption="O Gerente julgando seu estudo.", use_container_width=True)
        elif os.path.exists("gato1.jpeg"):
            st.image("gato1.jpeg", caption="O Gerente julgando seu estudo.", use_container_width=True)

    c_bot1, c_bot2 = st.columns(2)
    with c_bot1:
        if os.path.exists("gato2.jpeg"): st.image("gato2.jpeg", caption="Cochilo pós-deploy.", use_container_width=True)
    with c_bot2:
        if os.path.exists("gato3.jpeg"): st.image("gato3.jpeg", caption="Esperando o Pix.", use_container_width=True)

    st.markdown("### 💠 Chave Pix")
    st.markdown("""<div class="pix-container"><div class="pix-key">5b84b80d-c11a-4129-b897-74fb6371dfce</div></div>""", unsafe_allow_html=True)