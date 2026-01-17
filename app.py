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
    # Chave de fallback para testes locais
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

init_db()

# --- 4. CATÁLOGO PREMIUM (LINKS + VISUAL IMPACTANTE) ---
CATALOGO_PREMIUM = {
    "direito": {
        "links": [
            "https://amzn.to/4qJymYt", "https://amzn.to/4qAOVWf", "https://amzn.to/45jNwuK", 
            "https://amzn.to/4sKGLft", "https://amzn.to/4qslPZa"
        ],
        "visual": {
            "badge": "🔥 OFERTA JURÍDICA",
            "titulo": "KIT VADE MECUM & OAB",
            "subtitulo": "Os melhores materiais com preços imbatíveis.",
            "icone": "⚖️",
            # Gradiente Roxo/Dourado Luxo
            "bg_style": "background: rgb(75,20,140); background: linear-gradient(135deg, rgba(75,20,140,1) 0%, rgba(199,148,29,1) 100%);",
            "btn_color": "#FFD700", "btn_text": "#000"
        }
    },
    "tecnologia": {
        "links": [
            "https://amzn.to/4pJLkUC", "https://amzn.to/3LyNpVu", "https://amzn.to/49BErP3", 
            "https://amzn.to/4pFde4d", "https://amzn.to/4pCyW8J", "https://amzn.to/49Fvep3", 
            "https://amzn.to/49Ey5yr", "https://amzn.to/3LHtK5z", "https://amzn.to/4qxDgaS", 
            "https://amzn.to/49Egzue", "https://amzn.to/4aYslC1", "https://amzn.to/4qwxGW4", 
            "https://amzn.to/49HXuXY", "https://amzn.to/4bn0coz", "https://amzn.to/4b3nWOj", 
            "https://amzn.to/3LPR69e", "https://amzn.to/3NP6hQz", "https://amzn.to/3Zgb4Np", 
            "https://amzn.to/4quE3cz", "https://amzn.to/3NQ8fQE", "https://amzn.to/3YK4Fdd", 
            "https://amzn.to/45LnEbc", "https://amzn.to/4qs17sv", "https://amzn.to/3Nywpix", 
            "https://amzn.to/4pF9wr7", "https://amzn.to/4r44fe1"
        ],
        "visual": {
            "badge": "⚡ SETUP TECH",
            "titulo": "NOTEBOOKS & ACESSÓRIOS",
            "subtitulo": "Potencialize seus estudos com hardware de ponta.",
            "icone": "💻",
            # Gradiente Azul/Ciano Neon
            "bg_style": "background: rgb(0,108,255); background: linear-gradient(135deg, rgba(0,108,255,1) 0%, rgba(0,255,200,1) 100%);",
            "btn_color": "#FFF", "btn_text": "#000"
        }
    },
    "policial": {
        "links": [
            "https://amzn.to/4qPWLeq", "https://amzn.to/4jK4vMs", "https://amzn.to/4qXVCBy", 
            "https://amzn.to/4jOjNjx", "https://amzn.to/4qln2kV", "https://amzn.to/45cQFMP", 
            "https://amzn.to/3Nhq3En"
        ],
        "visual": {
            "badge": "🛡️ MISSÃO APROVAÇÃO",
            "titulo": "CARREIRAS POLICIAIS",
            "subtitulo": "Material tático e focado para o seu concurso.",
            "icone": "🚓",
            # Gradiente Laranja/Vermelho Alerta
            "bg_style": "background: rgb(255,69,0); background: linear-gradient(135deg, rgba(255,69,0,1) 0%, rgba(255,145,0,1) 100%);",
            "btn_color": "#FFF", "btn_text": "#FF4500"
        }
    },
    "geral": {
        "links": [
            "https://amzn.to/3NpLfYP", "https://amzn.to/49Z1vsr", "https://amzn.to/4sL9elk", 
            "https://amzn.to/4sKkRZD", "https://amzn.to/49Z1AML", "https://amzn.to/45X3YRE", 
            "https://amzn.to/4qSYWxD", "https://amzn.to/45Ym7yx", "https://amzn.to/4qYh0GT", 
            "https://amzn.to/4qXRrWb", "https://amzn.to/4qYh5KH", "https://amzn.to/49qnnwD", 
            "https://amzn.to/3Nvg91N", "https://amzn.to/4sHWTOM", "https://amzn.to/4sLF5SM", 
            "https://amzn.to/4sRPi0j", "https://amzn.to/4qX4BCS", "https://amzn.to/4r1JUWI", 
            "https://amzn.to/4riIes3", "https://amzn.to/4sPKZCK", "https://amzn.to/45fnwRd", 
            "https://amzn.to/4sIELnN", "https://amzn.to/4qqxg3r", "https://amzn.to/4quiOaK", 
            "https://amzn.to/3LvT7r9", "https://amzn.to/4qnkYZB", "https://amzn.to/4jKBAYV", 
            "https://amzn.to/4jM9FI6", "https://amzn.to/4jHMRci", "https://amzn.to/45eVftW", 
            "https://amzn.to/4quExiT", "https://amzn.to/45iqd4t", "https://amzn.to/4quiQPU", 
            "https://amzn.to/3Lnk93Y", "https://amzn.to/4bCsL16"
        ],
        "visual": {
            "badge": "🎁 SELEÇÃO ESPECIAL",
            "titulo": "ESSENCIAIS DO ESTUDANTE",
            "subtitulo": "Kindle, Fones e tudo para seu foco.",
            "icone": "🎒",
            # Gradiente Rosa/Roxo Moderno
            "bg_style": "background: rgb(255,0,168); background: linear-gradient(135deg, rgba(255,0,168,1) 0%, rgba(138,43,226,1) 100%);",
            "btn_color": "#FFF", "btn_text": "#8A2BE2"
        }
    }
}

def ia_escolher_categoria(contexto_usuario):
    """Usa IA ou contexto simples para definir a categoria do banner"""
    if not contexto_usuario or len(contexto_usuario) < 5:
        # Sem contexto, sorteia entre geral e tecnologia
        return random.choice(["geral", "tecnologia"])

    # Tenta usar IA se tiver chave
    if API_KEY:
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            # Prompt super rápido para classificar
            prompt = f"""Classifique o texto: "{contexto_usuario[:500]}"
            Categorias: direito, tecnologia, policial, geral.
            Responda APENAS a palavra da categoria em minúsculo."""
            
            resp = model.generate_content(prompt).text.strip().lower()
            
            if "direito" in resp: return "direito"
            if "tecnolo" in resp: return "tecnologia"
            if "policia" in resp: return "policial"
        except:
            pass # Se a IA falhar, cai no fallback abaixo

    # Fallback simples por palavra-chave se a IA falhar ou não tiver chave
    ctx_lower = contexto_usuario.lower()
    if any(x in ctx_lower for x in ["lei", "juridico", "oab", "penal"]): return "direito"
    if any(x in ctx_lower for x in ["python", "java", "código", "computador"]): return "tecnologia"
    if any(x in ctx_lower for x in ["policia", "militar", "taf"]): return "policial"
    
    return "geral"

# --- 5. CSS REVOLUCIONÁRIO (VISUAL DE VENDAS IMPACTANTE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #050505; }
    .stApp { background-color: #050505; }
    section[data-testid="stSidebar"] { background-color: #0F0F0F; border-right: 1px solid #222; }
    
    /* --- SUPER BANNER DE VENDAS --- */
    .super-banner {
        display: block;
        text-decoration: none;
        border-radius: 16px;
        padding: 20px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 2px solid rgba(255,255,255,0.1);
    }
    
    .super-banner:hover {
        transform: scale(1.03);
        box-shadow: 0 15px 40px rgba(0,0,0,0.7);
        border-color: rgba(255,255,255,0.3);
    }
    
    .sb-badge {
        position: absolute; top: 12px; right: 12px;
        background: rgba(0,0,0,0.6); color: #FFF;
        font-size: 0.7rem; font-weight: 900; padding: 4px 10px;
        border-radius: 20px; text-transform: uppercase; letter-spacing: 1px;
        backdrop-filter: blur(5px);
    }
    
    .sb-icon {
        font-size: 3.5rem; margin-bottom: 10px; display: block; text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .sb-title {
        color: #FFF; font-weight: 900; font-size: 1.4rem; line-height: 1.1;
        margin-bottom: 8px; display: block; text-transform: uppercase;
        text-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }
    
    .sb-subtitle {
        color: rgba(255,255,255,0.9); font-size: 0.9rem; display: block; margin-bottom: 20px; font-weight: 500;
    }
    
    .sb-button {
        background: #FFF; color: #000; text-align: center; font-weight: 800;
        padding: 12px 20px; border-radius: 50px; display: block;
        font-size: 1rem; transition: 0.2s; text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .sb-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }

    /* --- ESTILO PIX/APOIO --- */
    .pix-container {
        background: #111; border: 1px dashed #444; border-radius: 15px; padding: 30px; text-align: center;
    }
    .pix-key {
        font-family: monospace; background: #222; padding: 15px; border-radius: 8px;
        color: #00FF7F; font-size: 1.1rem; margin: 20px 0; word-break: break-all; select-all;
    }
    
    /* GERAL */
    .stButton button {
        text-align: left; padding: 12px; background: transparent; color: #999; 
        width: 100%; border: 1px solid transparent; border-radius: 8px !important; font-weight: 600;
    }
    .stButton button:hover { color: #FFF; background: #1A1A1A; border: 1px solid #333; }
    
    .questao-container {
        background-color: #111; border: 1px solid #333; border-left: 4px solid #333;
        padding: 30px; margin-bottom: 40px; border-radius: 0px;
    }
    .questao-texto { font-size: 1.2rem; line-height: 1.6; color: #FFF; margin-bottom: 25px; }
    .feedback-box { margin-top: 20px; padding: 20px; }
    .feedback-correct { background-color: #051B11; border-left: 4px solid #198754; color: #75B798; }
    .feedback-wrong { background-color: #2C0B0E; border-left: 4px solid #DC3545; color: #EA868F; }
    
    input[type="text"] { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. GERENCIAMENTO DE ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state: st.session_state.chat_ativo_id = None
if "editando_id" not in st.session_state: st.session_state.editando_id = None
if "mensagens_ia" not in st.session_state: st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA."}]

# --- 7. FUNÇÕES ---
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

# --- 8. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: Inter; font-weight: 900; letter-spacing: -1px;'>Pratica.ai <span style='color:#444'>.</span></h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navegação Principal
    if st.button("📄 NOVO UPLOAD", use_container_width=True):
        st.session_state.pagina_atual = "upload"; st.session_state.chat_ativo_id = None; st.rerun()
        
    if st.button("🤖 TUTOR IA", use_container_width=True):
        st.session_state.pagina_atual = "chat_ia"; st.session_state.chat_ativo_id = None; st.rerun()

    if st.button("🐱 APOIE NOSSO PROJETO", use_container_width=True):
        st.session_state.pagina_atual = "apoio"; st.session_state.chat_ativo_id = None; st.rerun()
    
    # --- ÁREA DO SUPER BANNER DE VENDAS (CONTEXTUAL) ---
    st.markdown("---")
    st.markdown("<p style='font-size: 0.75rem; color: #888; font-weight: 800; letter-spacing: 1px; margin-bottom: 10px;'>PATROCINADO</p>", unsafe_allow_html=True)
    
    # 1. Detectar Contexto
    contexto_usuario = ""
    if st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo: contexto_usuario = estudo_ativo['titulo']
    elif st.session_state.pagina_atual == "chat_ia" and len(st.session_state.mensagens_ia) > 1:
             contexto_usuario = st.session_state.mensagens_ia[-2]['content']

    # 2. Escolher Categoria e Link
    cat_nome = ia_escolher_categoria(contexto_usuario)
    cat_data = CATALOGO_PREMIUM[cat_nome]
    link_final = random.choice(cat_data["links"])
    visual = cat_data["visual"]

    # 3. Renderizar o SUPER BANNER
    st.markdown(f"""
    <a href="{link_final}" target="_blank" class="super-banner" style="{visual['bg_style']}">
        <div class="sb-badge">{visual['badge']}</div>
        <span class="sb-icon">{visual['icone']}</span>
        <span class="sb-title">{visual['titulo']}</span>
        <span class="sb-subtitle">{visual['subtitulo']}</span>
        <span class="sb-button" style="background: {visual['btn_color']}; color: {visual['btn_text']};">VER OFERTA AGORA</span>
    </a>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Biblioteca
    st.markdown("<p style='font-size: 0.7rem; color: #666; text-transform: uppercase; font-weight: bold;'>Sua Biblioteca</p>", unsafe_allow_html=True)
    for estudo in st.session_state.historico:
        if st.session_state.editando_id == estudo["id"]:
            def salvar_nome(): st.session_state.editando_id = None
            novo_nome = st.text_input("Nome:", value=estudo["titulo"], key=f"input_{estudo['id']}", on_change=salvar_nome)
            estudo["titulo"] = novo_nome 
            if st.button("Salvar", key=f"save_{estudo['id']}"):
                salvar_estudo_bd(estudo); st.session_state.editando_id = None; st.rerun()
        else:
            col_nav, col_edit = st.columns([5, 1])
            with col_nav:
                icone = "📂" if st.session_state.chat_ativo_id == estudo["id"] else "📁"
                if st.button(f"{icone} {estudo['titulo']}", key=f"btn_{estudo['id']}", use_container_width=True):
                    st.session_state.chat_ativo_id = estudo["id"]; st.session_state.pagina_atual = "visualizacao"; st.rerun()
            with col_edit:
                if st.button("✎", key=f"edit_{estudo['id']}"): st.session_state.editando_id = estudo["id"]; st.rerun()

# --- 9. ÁREA PRINCIPAL ---

# >>> PÁGINA 1: UPLOAD <<<
if st.session_state.pagina_atual == "upload":
    st.markdown("""
    <div style="text-align: left; margin-top: 80px;">
        <h1 style="font-size: 4rem; color: #FFF; font-weight: 900; letter-spacing: -2px;">PRATICA<span style="color: #444;">.AI</span></h1>
        <p style="color: #888; font-size: 1.2rem; font-weight: 500;">A melhor forma de estudar, potencializada por IA.</p>
    </div>
    """, unsafe_allow_html=True)
    col_up, _ = st.columns([1, 1])
    with col_up:
        st.markdown("<br>", unsafe_allow_html=True)
        modo = st.radio("O QUE VAMOS FAZER?", ["Criar Questões", "Extrair Prova"])
        arquivo = st.file_uploader("ARRASTE SEU PDF", type="pdf")
        if arquivo and st.button("PROCESSAR ->", type="primary"):
            with st.spinner("LENDO ARQUIVO..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes); st.rerun()
                    else: st.error("Erro ao processar.")

# >>> PÁGINA 2: APOIO (PIX & GATOS) <<<
elif st.session_state.pagina_atual == "apoio":
    st.title("🐱 Apoie o Projeto (e o Gatinho)")
    
    st.markdown("""
    <h3 style="color: #CCC;">O site é 100% grátis!</h3>
    Mas se ele te ajudou nos estudos e você quiser pagar um sachê para o nosso <b>Gerente de TI (o gato das fotos)</b>, ficaremos muito felizes!
    """, unsafe_allow_html=True)
    
    # GALERIA DE FOTOS DO GATO
    cols_gato = st.columns(3)
    fotos_gato = ["gato1.jpeg", "gato2.jpeg", "gato3.jpeg"] # Lembre de colocar os arquivos na pasta!
    caption_gato = ["O Gerente julgando seu estudo.", "Tirando um cochilo pós-deploy.", "Esperando o Pix do sachê."]
    
    for i, foto in enumerate(fotos_gato):
        with cols_gato[i]:
            if os.path.exists(foto):
                st.image(foto, caption=caption_gato[i], use_column_width=True)
            else:
                st.warning(f"📸 Foto {foto} não encontrada na pasta.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💠 Chave Pix Copia e Cola")
    st.markdown("""
    <div class="pix-container">
        <p style="color: #888; margin-bottom: 10px;">Clique duas vezes na chave abaixo para copiar:</p>
        <div class="pix-key">5b84b80d-c11a-4129-b897-74fb6371dfce</div>
        <p style="margin-top: 20px; color: #FFF;"><i>Obrigado por apoiar a educação! ❤️</i></p>
    </div>
    """, unsafe_allow_html=True)


# >>> PÁGINA 3: TUTOR IA <<<
elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA")
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
                    response = model.generate_content(f"Seja didático. Usuário: {prompt}")
                    st.markdown(response.text)
                    st.session_state.mensagens_ia.append({"role": "model", "content": response.text})
    else:
        st.info("Digite um tema para gerar um simulado completo.")
        if assunto := st.chat_input("Ex: Direito Constitucional..."):
            with st.spinner(f"Criando: {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                if questoes: criar_novo_estudo(f"Simulado: {assunto}", questoes); st.rerun()

# >>> PÁGINA 4: VISUALIZAÇÃO DO SIMULADO <<<
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