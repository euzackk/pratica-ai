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

# --- 5. CSS (VISUAL SQUARED/QUADRADO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #050505; }
    .stApp { background-color: #050505; }
    section[data-testid="stSidebar"] { background-color: #0F0F0F; border-right: 1px solid #222; }
    
    /* GERAL QUADRADO (SQUARED) */
    .stButton button, img, .super-banner, .lib-card, .amazon-card, input, .pix-container, .questao-container {
        border-radius: 0px !important;
    }

    /* SUPER BANNER LATERAL */
    .super-banner {
        display: block; text-decoration: none; padding: 20px; margin: 20px 0;
        position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: transform 0.3s ease; border: 1px solid rgba(255,255,255,0.1);
    }
    .super-banner:hover { transform: scale(1.02); border-color: #FFF; }
    .sb-badge { position: absolute; top: 0; right: 0; background: #000; color: #FFF; font-size: 0.6rem; font-weight: 900; padding: 5px 10px; }
    .sb-icon { font-size: 3rem; margin-bottom: 10px; display: block; }
    .sb-title { color: #FFF; font-weight: 900; font-size: 1.2rem; line-height: 1.1; margin-bottom: 5px; display: block; }
    .sb-subtitle { color: rgba(255,255,255,0.8); font-size: 0.8rem; display: block; margin-bottom: 15px; }
    .sb-button { background: #FFF; color: #000; text-align: center; font-weight: 800; padding: 10px; display: block; font-size: 0.9rem; text-transform: uppercase; border: none; }

    /* CARD BIBLIOTECA */
    .lib-card {
        background: #111; border: 1px solid #333; padding: 20px;
        transition: 0.2s; cursor: pointer; text-align: left; height: 100%;
        border-left: 4px solid #333;
    }
    .lib-card:hover { border-color: #555; background: #161616; border-left-color: #F0C14B; }
    .lib-title { font-weight: 700; color: #FFF; font-size: 1rem; margin-bottom: 5px; }
    .lib-date { color: #666; font-size: 0.8rem; }
    .lib-icon { font-size: 1.5rem; float: right; opacity: 0.5; }

    /* PIX & GATOS */
    .pix-container { background: #111; border: 1px dashed #444; padding: 30px; text-align: center; }
    .pix-key { font-family: monospace; background: #222; padding: 15px; color: #00FF7F; font-size: 1.1rem; margin: 20px 0; word-break: break-all; select-all; }
    
    /* QUESTÕES */
    .stButton button { text-align: left; background: transparent; color: #DDD; width: 100%; border: 1px solid transparent; }
    .stButton button:hover { background: #222; border: 1px solid #333; }
    .questao-container { background-color: #111; border: 1px solid #333; border-left: 4px solid #333; padding: 30px; margin-bottom: 40px; }
    .feedback-correct { background-color: #051B11; border-left: 4px solid #198754; color: #75B798; padding: 15px; margin-top: 10px;}
    .feedback-wrong { background-color: #2C0B0E; border-left: 4px solid #DC3545; color: #EA868F; padding: 15px; margin-top: 10px;}
    
    /* LOJA */
    .amazon-card { background: #FFF; padding: 15px; text-align: center; display: block; text-decoration: none; border: 1px solid #DDD; }
    .amz-button { background: #FFD814; color: #000; padding: 8px; display: block; margin-top: 10px; font-weight: bold; }
    
    /* ABAS CUSTOMIZADAS */
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] { border-radius: 0px; background-color: #111; color: #666; border: 1px solid #333; border-bottom: none; }
    .stTabs [aria-selected="true"] { background-color: #000 !important; color: #FFF !important; border-top: 3px solid #FFF !important; }

</style>
""", unsafe_allow_html=True)

# --- 6. GERENCIAMENTO DE ESTADO ---
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
    st.session_state.pagina_atual = "biblioteca" # Vai direto pra aba de estudos
    st.rerun()

# --- 8. BARRA LATERAL (NAVEGAÇÃO + VENDAS) ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: Inter; font-weight: 900; letter-spacing: -1px;'>Pratica.ai <span style='color:#F0C14B'>.</span></h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navegação
    if st.button("📄 NOVO UPLOAD", use_container_width=True): st.session_state.pagina_atual = "upload"; st.rerun()
    if st.button("📚 BIBLIOTECA", use_container_width=True): st.session_state.pagina_atual = "biblioteca"; st.rerun()
    if st.button("🤖 TUTOR IA", use_container_width=True): st.session_state.pagina_atual = "chat_ia"; st.rerun()
    if st.button("🛒 LOJA", use_container_width=True): st.session_state.pagina_atual = "loja"; st.rerun()
    if st.button("🐱 APOIE (PIX)", use_container_width=True): st.session_state.pagina_atual = "apoio"; st.rerun()
    
    st.markdown("---")
    
    # Super Banner de Vendas (IA Contextual)
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

    st.markdown("<p style='font-size: 0.7rem; color: #666; font-weight: 800; letter-spacing: 1px;'>PATROCINADO</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <a href="{link_final}" target="_blank" class="super-banner" style="{visual['bg_style']}">
        <div class="sb-badge">{visual['badge']}</div>
        <span class="sb-icon">{visual['icone']}</span>
        <span class="sb-title">{visual['titulo']}</span>
        <span class="sb-subtitle">{visual['subtitulo']}</span>
        <span class="sb-button" style="background: {visual['btn_color']}; color: {visual['btn_text']};">VER OFERTA</span>
    </a>
    """, unsafe_allow_html=True)

# --- 9. ÁREA PRINCIPAL ---

# >>> PÁGINA 1: UPLOAD <<<
if st.session_state.pagina_atual == "upload":
    st.markdown("""
    <div style="text-align: left; margin-top: 50px;">
        <h1 style="font-size: 4rem; color: #FFF; font-weight: 900; letter-spacing: -2px;">PRATICA<span style="color: #444;">.AI</span></h1>
        <p style="color: #888; font-size: 1.2rem;">Inteligência Artificial para Concursos.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<br>", unsafe_allow_html=True)
        modo = st.radio("MODO:", ["Criar Questões", "Extrair Prova"])
        arquivo = st.file_uploader("ARRASTE SEU PDF", type="pdf")
        if arquivo and st.button("PROCESSAR ->", type="primary"):
            with st.spinner("LENDO ARQUIVO..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes)
                    else: st.error("Erro ao processar.")

# >>> PÁGINA 2: BIBLIOTECA (COM ABAS NO TOPO) <<<
elif st.session_state.pagina_atual == "biblioteca":
    
    # Determina quais abas mostrar
    abas_titulos = ["📂 Todos os Arquivos"]
    estudo_ativo = None
    
    # Se tiver um estudo ativo, cria uma aba para ele
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo:
            abas_titulos.append(f"📝 {estudo_ativo['titulo']}")
            
    # Cria as abas no topo
    abas = st.tabs(abas_titulos)
    
    # ABA 1: LISTA DE ARQUIVOS
    with abas[0]:
        st.title("Minha Biblioteca")
        if not st.session_state.historico:
            st.info("Nenhum estudo encontrado.")
        else:
            cols = st.columns(3)
            for i, estudo in enumerate(st.session_state.historico):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="lib-card">
                        <div class="lib-icon">📄</div>
                        <div class="lib-title">{estudo['titulo']}</div>
                        <div class="lib-date">{estudo['data']} • {len(estudo['questoes'])} questões</div>
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
                            if st.session_state.chat_ativo_id == estudo['id']: st.session_state.chat_ativo_id = None
                            st.session_state.historico = carregar_historico_bd()
                            st.rerun()

    # ABA 2: ESTUDO ABERTO (Se houver)
    if estudo_ativo and len(abas) > 1:
        with abas[1]:
            st.markdown(f"## {estudo_ativo['titulo']}")
            if st.button("⬅ Fechar Estudo"):
                st.session_state.chat_ativo_id = None
                st.rerun()
                
            st.markdown("---")
            for index, q in enumerate(estudo_ativo['questoes']):
                st.markdown(f"""
                <div class="questao-container">
                    <div style="color: #666; font-size: 0.8rem; margin-bottom: 10px;">QUESTÃO {index + 1:02d}</div>
                    <div class="questao-texto">{q['pergunta']}</div>
                </div>""", unsafe_allow_html=True)
                
                res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
                idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
                escolha = st.radio("Alternativas:", q['opcoes'], index=idx, key=f"q_{estudo_ativo['id']}_{q['id']}", label_visibility="collapsed")
                
                if escolha and escolha != res_salva:
                    estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                    salvar_estudo_bd(estudo_ativo); st.rerun()
                
                if res_salva:
                    letra_user = res_salva.split(")")[0].strip().upper()
                    letra_correta = q['correta'].strip().upper()
                    if letra_user == letra_correta: st.markdown(f"""<div class="feedback-correct"><b>✓ ACERTOU</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                    else: st.markdown(f"""<div class="feedback-wrong"><b>✕ ERROU (Correta: {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("↺ Reiniciar Simulado", use_container_width=True):
                estudo_ativo["respostas_usuario"] = {}
                salvar_estudo_bd(estudo_ativo); st.rerun()


# >>> PÁGINA 3: TUTOR IA <<<
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

# >>> PÁGINA 4: LOJA <<<
elif st.session_state.pagina_atual == "loja":
    st.title("🛒 Loja Oficial")
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

# >>> PÁGINA 5: APOIO (PIRÂMIDE GATOS) <<<
elif st.session_state.pagina_atual == "apoio":
    st.title("🐱 Apoie o Projeto")
    st.markdown("<h3 style='color: #CCC;'>Ajude a manter o servidor ligado!</h3>", unsafe_allow_html=True)
    
    # LAYOUT PIRÂMIDE CENTRALIZADA
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("static/gato1.jpeg"): st.image("static/gato1.jpeg", caption="Gerente Julgando.", use_container_width=True)
        elif os.path.exists("gato1.jpeg"): st.image("gato1.jpeg", caption="Gerente Julgando.", use_container_width=True)
    
    c_base1, c_base2 = st.columns(2)
    with c_base1:
        if os.path.exists("static/gato2.jpeg"): st.image("static/gato2.jpeg", caption="Cochilo.", use_container_width=True)
        elif os.path.exists("gato2.jpeg"): st.image("gato2.jpeg", caption="Cochilo.", use_container_width=True)
    with c_base2:
        if os.path.exists("static/gato3.jpeg"): st.image("static/gato3.jpeg", caption="Esperando Pix.", use_container_width=True)
        elif os.path.exists("gato3.jpeg"): st.image("gato3.jpeg", caption="Esperando Pix.", use_container_width=True)

    st.markdown("<br><div class='pix-container'><div class='pix-key'>5b84b80d-c11a-4129-b897-74fb6371dfce</div></div>", unsafe_allow_html=True)