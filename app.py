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
    # Coloque sua chave aqui apenas para testes locais
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

# --- 4. SISTEMA DE AFILIADOS COM IA (SEUS LINKS) ---

# Banco de Links Organizado com base na sua lista
LINKS_AFILIADOS = {
    "direito": [
        "https://amzn.to/4qJymYt", "https://amzn.to/4qAOVWf", "https://amzn.to/45jNwuK", 
        "https://amzn.to/4sKGLft", "https://amzn.to/4qslPZa"
    ],
    "tecnologia": [
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
    "policial": [
        "https://amzn.to/4qPWLeq", "https://amzn.to/4jK4vMs", "https://amzn.to/4qXVCBy", 
        "https://amzn.to/4jOjNjx", "https://amzn.to/4qln2kV", "https://amzn.to/45cQFMP", 
        "https://amzn.to/3Nhq3En"
    ],
    "geral": [
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
    ]
}

# Informações visuais para o banner
INFO_CATEGORIA = {
    "direito": {"titulo": "⚖️ Seleção Jurídica", "desc": "Vade Mecums e livros essenciais para seus estudos."},
    "tecnologia": {"titulo": "💻 Tech & Produtividade", "desc": "Equipamentos de alta performance recomendados."},
    "policial": {"titulo": "🛡️ Carreiras Policiais", "desc": "Material tático e apostilas focadas."},
    "geral": {"titulo": "🎒 Ofertas para Estudantes", "desc": "Kindle, acessórios e itens essenciais."}
}

def ia_escolher_anuncio(contexto_usuario):
    """
    Usa a IA (Gemini) como Gerente de Marketing.
    Ela analisa o que o usuário está fazendo e decide qual produto ofertar.
    """
    if not contexto_usuario or len(contexto_usuario) < 5:
        # Se não tiver contexto, sorteia geral ou tecnologia
        cat = random.choice(["geral", "tecnologia"])
        return cat, random.choice(LINKS_AFILIADOS[cat])

    model = genai.GenerativeModel('gemini-flash-latest')
    
    # Prompt de Marketing Contextual
    prompt = f"""
    Atue como um sistema de recomendação de anúncios inteligente.
    
    Contexto do Usuário (o que ele está estudando/lendo): 
    "{contexto_usuario[:800]}"
    
    Temos 4 categorias de produtos para vender:
    1. direito (Vade Mecum, livros de lei)
    2. tecnologia (Notebooks, teclados, mouse)
    3. policial (Apostilas para policia, itens táticos)
    4. geral (Kindle, roupas, academia, fones)
    
    Com base no contexto, qual categoria tem a MAIOR chance de conversão?
    Responda APENAS a palavra da categoria em minúsculo. Se nada bater, responda 'geral'.
    """
    
    try:
        response = model.generate_content(prompt)
        categoria_ia = response.text.strip().lower()
        
        # Limpeza caso a IA responda algo fora do padrão
        if "direito" in categoria_ia: categoria_ia = "direito"
        elif "tecnologia" in categoria_ia: categoria_ia = "tecnologia"
        elif "policial" in categoria_ia: categoria_ia = "policial"
        elif "geral" in categoria_ia: categoria_ia = "geral"
        else: categoria_ia = "geral"
            
    except:
        categoria_ia = "geral"

    # Retorna a categoria e um link aleatório daquela lista
    return categoria_ia, random.choice(LINKS_AFILIADOS[categoria_ia])

# --- 5. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E0E0; background-color: #000000; }
    .stApp { background-color: #000000; }
    section[data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #333; }
    
    .stButton button {
        text-align: left; padding: 10px; border: 1px solid transparent;
        background: transparent; color: #888; width: 100%; border-radius: 0px !important;
    }
    .stButton button:hover { color: #FFF; background: #1A1A1A; border: 1px solid #333; }
    
    .questao-container {
        background-color: #111; border: 1px solid #333; border-left: 4px solid #333;
        padding: 30px; margin-bottom: 40px; border-radius: 0px;
    }
    .questao-header { font-family: 'JetBrains Mono'; color: #666; font-size: 0.75rem; letter-spacing: 2px; margin-bottom: 15px; }
    .questao-texto { font-size: 1.2rem; line-height: 1.6; color: #FFF; margin-bottom: 25px; }
    
    .feedback-box { margin-top: 20px; padding: 20px; font-size: 0.95rem; animation: fadeIn 0.5s; }
    .feedback-correct { background-color: #051B11; border: 1px solid #0F5132; border-left: 4px solid #198754; color: #75B798; }
    .feedback-wrong { background-color: #2C0B0E; border: 1px solid #842029; border-left: 4px solid #DC3545; color: #EA868F; }
    
    /* ANÚNCIOS INTELIGENTES */
    .ad-card {
        display: block; padding: 15px; margin: 15px 0;
        background: linear-gradient(145deg, #161616, #0A0A0A); 
        border: 1px solid #333; color: #CCC;
        text-decoration: none; font-size: 0.9rem; transition: 0.3s;
        text-align: left; border-radius: 0px;
        position: relative; overflow: hidden;
    }
    .ad-card:hover { border-color: #58a6ff; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .ad-tag { 
        font-size: 0.6rem; color: #000; background: #EEE; 
        padding: 2px 6px; font-weight: bold;
        display: inline-block; margin-bottom: 8px; font-family: 'JetBrains Mono';
    }
    .ad-title { color: #FFF; font-weight: bold; font-size: 1rem; margin-bottom: 4px; display: block; }
    .ad-desc { font-size: 0.8rem; color: #888; }
    .pix-box { font-family: 'JetBrains Mono'; background: #222; padding: 10px; font-size: 0.8rem; color: #FFF; border: 1px dashed #555; word-break: break-all; }
    
    input[type="text"], input[type="password"] { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }
    .stRadio label { color: #CCC !important; }
    .small-btn button { padding: 5px !important; text-align: center; font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. GERENCIAMENTO DE ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state: st.session_state.chat_ativo_id = None
if "editando_id" not in st.session_state: st.session_state.editando_id = None
if "mensagens_ia" not in st.session_state: st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA. Pode me pedir questões ou tirar dúvidas."}]

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

# --- 8. BARRA LATERAL (COM IA DE VENDAS) ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-family: JetBrains Mono;'>Pratica.ai_</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("＋ NOVO UPLOAD", use_container_width=True):
        st.session_state.pagina_atual = "upload"
        st.session_state.chat_ativo_id = None
        st.rerun()
        
    if st.button("🤖 TUTOR IA", use_container_width=True):
        st.session_state.pagina_atual = "chat_ia"
        st.session_state.chat_ativo_id = None
        st.rerun()
    
    st.markdown("<br><p style='font-size: 0.8rem; color: #666; text-transform: uppercase;'>Biblioteca</p>", unsafe_allow_html=True)
    
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
                icone = "■" if st.session_state.chat_ativo_id == estudo["id"] else "□"
                if st.button(f"{icone} {estudo['titulo']}", key=f"btn_{estudo['id']}", use_container_width=True):
                    st.session_state.chat_ativo_id = estudo["id"]
                    st.session_state.pagina_atual = "visualizacao"
                    st.rerun()
            with col_edit:
                st.markdown('<div class="small-btn">', unsafe_allow_html=True)
                if st.button("✎", key=f"edit_{estudo['id']}"):
                    st.session_state.editando_id = estudo["id"]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # --- LÓGICA DE RECOMENDAÇÃO AUTOMÁTICA (AI POWERED) ---
    # 1. Determina o contexto
    contexto_usuario = ""
    
    if st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo:
            contexto_usuario = estudo_ativo['titulo']
            
    elif st.session_state.pagina_atual == "chat_ia":
        if len(st.session_state.mensagens_ia) > 1:
             for msg in reversed(st.session_state.mensagens_ia):
                 if msg['role'] == 'user':
                     contexto_usuario = msg['content']
                     break

    # 2. IA escolhe o anúncio
    cat_escolhida, link_escolhido = ia_escolher_anuncio(contexto_usuario)
    info_visual = INFO_CATEGORIA[cat_escolhida]

    # 3. Exibe o anúncio
    st.markdown("---")
    st.markdown(f"""
    <a href="{link_escolhido}" target="_blank" class="ad-card">
        <span class="ad-tag">RECOMENDADO PELA IA</span>
        <span class="ad-title">{info_visual['titulo']}</span>
        <span class="ad-desc">{info_visual['desc']}</span>
    </a>
    """, unsafe_allow_html=True)

    # 4. Doação Pix
    with st.expander("💖 Apoie o Projeto"):
        st.write("Sua doação mantém o servidor!")
        st.caption("Chave Pix Aleatória:")
        st.markdown(f"<div class='pix-box'>5b84b80d-c11a-4129-b897-74fb6371dfce</div>", unsafe_allow_html=True)

# --- 9. ÁREA PRINCIPAL ---
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
        modo = st.radio("MODO:", ["Criar Questões do PDF", "Extrair Prova do PDF"])
        st.markdown("<br>", unsafe_allow_html=True)
        arquivo = st.file_uploader("ARRASTE SEU PDF AQUI", type="pdf")
        if arquivo and st.button("PROCESSAR (GRÁTIS) ->", type="primary"):
            with st.spinner("ANALISANDO DADOS..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes); st.rerun()
                    else: st.error("Erro ao processar.")

elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA (Gratuito)")
    
    # REMOVIDO BLOQUEIO (FREE PARA TODOS)
    modo_tutor = st.radio("MODO:", ["💬 Chat", "📝 Gerar Simulado"], horizontal=True)
    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
    
    if modo_tutor == "💬 Chat":
        for msg in st.session_state.mensagens_ia:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role): st.markdown(msg["content"])
        if prompt := st.chat_input("Pergunte algo..."):
            st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    model = genai.GenerativeModel('gemini-flash-latest')
                    response = model.generate_content(f"Seja didático. Usuário: {prompt}")
                    st.markdown(response.text)
                    st.session_state.mensagens_ia.append({"role": "model", "content": response.text})
    else:
        st.info("Digite um assunto para criar uma prova instantânea.")
        if assunto := st.chat_input("Ex: Direito Penal, Python..."):
            with st.spinner(f"Criando: {assunto}..."):
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
                <div class="questao-header">QUESTÃO {index + 1:02d}</div>
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
                if letra_user == letra_correta: st.markdown(f"""<div class="feedback-box feedback-correct"><b>✓ CORRETO</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                else: st.markdown(f"""<div class="feedback-box feedback-wrong"><b>✕ ERRADO (A correta é {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)