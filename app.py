import streamlit as st
import google.generativeai as genai
import pypdf
import json
import uuid
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE SEGURANÇA ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY = "AIzaSyAq0c34TLlblT-a6ysdDr07edPBfnqR4kA" # Fallback local

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. SETUP DA PÁGINA ---
st.set_page_config(
    page_title="Pratica.ai",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. BANCO DE DADOS (PERSISTÊNCIA) ---
def init_db():
    """Cria a tabela se não existir"""
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    # Tabela de Estudos
    c.execute('''CREATE TABLE IF NOT EXISTS estudos
                 (id TEXT PRIMARY KEY, titulo TEXT, data TEXT, questoes TEXT, respostas TEXT)''')
    conn.commit()
    conn.close()

def carregar_historico_bd():
    """Lê do banco e joga para o session_state"""
    conn = sqlite3.connect('dados_pratica.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM estudos ORDER BY data DESC")
    rows = c.fetchall()
    
    lista_estudos = []
    for row in rows:
        lista_estudos.append({
            "id": row["id"],
            "titulo": row["titulo"],
            "data": row["data"],
            "questoes": json.loads(row["questoes"]),
            "respostas_usuario": json.loads(row["respostas"])
        })
    conn.close()
    return lista_estudos

def salvar_estudo_bd(estudo):
    """Salva ou atualiza um estudo no banco"""
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO estudos (id, titulo, data, questoes, respostas)
                 VALUES (?, ?, ?, ?, ?)''', 
                 (estudo["id"], estudo["titulo"], estudo["data"], 
                  json.dumps(estudo["questoes"]), json.dumps(estudo["respostas_usuario"])))
    conn.commit()
    conn.close()

def deletar_estudo_bd(id_estudo):
    """Remove do banco"""
    conn = sqlite3.connect('dados_pratica.db')
    c = conn.cursor()
    c.execute("DELETE FROM estudos WHERE id=?", (id_estudo,))
    conn.commit()
    conn.close()

# Inicializa o banco ao rodar o script
init_db()

# --- 4. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #000000;
    }
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
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    
    input[type="text"] { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }
    .stRadio label { color: #CCC !important; }
    .small-btn button { padding: 5px !important; text-align: center; font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. GERENCIAMENTO DE ESTADO ---
# Carrega do banco sempre que a página carrega
if "historico" not in st.session_state:
    st.session_state.historico = carregar_historico_bd()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state:
    st.session_state.chat_ativo_id = None
if "editando_id" not in st.session_state:
    st.session_state.editando_id = None
if "mensagens_ia" not in st.session_state:
    st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA."}]

# --- 6. FUNÇÕES ---
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
        "id": novo_id,
        "titulo": nome_arquivo,
        "data": datetime.now().strftime("%d/%m"),
        "questoes": questoes,
        "respostas_usuario": {} 
    }
    # Salva no banco imediatamente
    salvar_estudo_bd(novo_estudo)
    # Atualiza estado local
    st.session_state.historico = carregar_historico_bd()
    st.session_state.chat_ativo_id = novo_id
    st.session_state.pagina_atual = "visualizacao"

def atualizar_progresso(estudo):
    # Função auxiliar para salvar progresso a cada clique
    salvar_estudo_bd(estudo)

# --- 7. BARRA LATERAL ---
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
            def salvar_nome():
                st.session_state.editando_id = None
            novo_nome = st.text_input("Nome:", value=estudo["titulo"], key=f"input_{estudo['id']}", on_change=salvar_nome)
            estudo["titulo"] = novo_nome 
            if st.button("Salvar", key=f"save_{estudo['id']}"):
                salvar_estudo_bd(estudo) # Salva nome no banco
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

# --- 8. ÁREA PRINCIPAL ---
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
        
        if arquivo and st.button("PROCESSAR ->", type="primary"):
            with st.spinner("ANALISANDO DADOS..."):
                texto, erro = ler_pdf(arquivo)
                if erro: st.error(erro)
                else:
                    tipo = "criar" if "Criar" in modo else "extrair"
                    questoes = chamar_ia_json(texto, tipo)
                    if questoes: criar_novo_estudo(arquivo.name, questoes); st.rerun()
                    else: st.error("Erro ao processar.")

elif st.session_state.pagina_atual == "chat_ia":
    st.title("🤖 Tutor IA")
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
                if questoes:
                    criar_novo_estudo(f"Simulado: {assunto}", questoes)
                    st.rerun()

elif st.session_state.pagina_atual == "visualizacao" and st.session_state.chat_ativo_id:
    # Busca o estudo ATUALIZADO da lista (que veio do BD)
    estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
    
    if estudo_ativo:
        c1, c2 = st.columns([5, 1])
        with c1: st.title(estudo_ativo['titulo'])
        with c2:
            if st.button("↺ REINICIAR", use_container_width=True):
                estudo_ativo["respostas_usuario"] = {}
                salvar_estudo_bd(estudo_ativo) # Salva o reset
                st.rerun()

        st.markdown("<div style='height: 1px; background-color: #333; margin-bottom: 40px;'></div>", unsafe_allow_html=True)

        for index, q in enumerate(estudo_ativo['questoes']):
            st.markdown(f"""
            <div class="questao-container">
                <div class="questao-header">QUESTÃO {index + 1:02d}</div>
                <div class="questao-texto">{q['pergunta']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            res_salva = estudo_ativo["respostas_usuario"].get(str(q['id']))
            idx = q['opcoes'].index(res_salva) if res_salva in q['opcoes'] else None
            
            escolha = st.radio("Alternativas:", q['opcoes'], index=idx, key=f"r_{estudo_ativo['id']}_{q['id']}", label_visibility="collapsed")

            if escolha and escolha != res_salva:
                estudo_ativo["respostas_usuario"][str(q['id'])] = escolha
                atualizar_progresso(estudo_ativo) # Salva no banco a cada clique!
                st.rerun() # Recarrega para mostrar o feedback

            # Mostra feedback se tiver resposta salva
            if res_salva:
                letra_user = res_salva.split(")")[0].strip().upper()
                letra_correta = q['correta'].strip().upper()
                if letra_user == letra_correta:
                    st.markdown(f"""<div class="feedback-box feedback-correct"><b>✓ CORRETO</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="feedback-box feedback-wrong"><b>✕ ERRADO (A correta é {letra_correta})</b><br>{q['comentario']}</div>""", unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)