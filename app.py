import streamlit as st
import google.generativeai as genai
import pypdf
import json
import uuid
import sqlite3
import random
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO INICIAL (Obrigatório ser o primeiro comando) ---
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "auto"

st.set_page_config(
    page_title="Pratica.ai",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 2. CONFIGURAÇÃO DE SEGURANÇA ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY = None

if API_KEY:
    genai.configure(api_key=API_KEY)

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

# --- 4. FUNÇÃO DE NAVEGAÇÃO (CALLBACK) ---
# Esta função roda quando o botão é clicado, ANTES da página recarregar.
def navegar(pagina):
    st.session_state.pagina_atual = pagina
    st.session_state.sidebar_state = "collapsed"  # Força o fechamento do menu

# --- 5. CATÁLOGO DE VENDAS ---
CATALOGO_PREMIUM = {
    "direito": {
        "visual": {"badge": "🔥 OFERTA", "titulo": "KIT OAB 2026", "icone": "⚖️", "bg_style": "background: linear-gradient(135deg, #240b36 0%, #c31432 100%);", "btn_text": "VER PREÇO"},
        "produtos": [
            {"nome": "Vade Mecum Saraiva 2026", "link": "https://amzn.to/4qJymYt"},
            {"nome": "Vade Mecum Rideel Compacto", "link": "https://amzn.to/4qAOVWf"}
        ]
    },
    "tecnologia": {
        "visual": {"badge": "⚡ SETUP", "titulo": "NOTEBOOKS & GAMER", "icone": "💻", "bg_style": "background: linear-gradient(135deg, #000428 0%, #004e92 100%);", "btn_text": "CONFIRMAR"},
        "produtos": [
            {"nome": "Notebook Acer Aspire 5", "link": "https://amzn.to/4pJLkUC"},
            {"nome": "Mouse Logitech MX Master", "link": "https://amzn.to/3LyNpVu"}
        ]
    },
    "policial": {
        "visual": {"badge": "🛡️ TÁTICO", "titulo": "KIT POLÍCIA", "icone": "🚓", "bg_style": "background: linear-gradient(135deg, #16222A 0%, #3A6073 100%);", "btn_text": "EQUIPAMENTOS"},
        "produtos": [
            {"nome": "Apostila Alfacon Policial", "link": "https://amzn.to/4qPWLeq"},
            {"nome": "Coturno Tático Militar", "link": "https://amzn.to/4qXVCBy"}
        ]
    },
    "geral": {
        "visual": {"badge": "🎁 PROMO", "titulo": "KINDLE & FOCO", "icone": "🎒", "bg_style": "background: linear-gradient(135deg, #1A2980 0%, #26D0CE 100%);", "btn_text": "APROVEITAR"},
        "produtos": [
            {"nome": "Kindle 11ª Geração", "link": "https://amzn.to/3NpLfYP"},
            {"nome": "Fone JBL Cancelamento Ruído", "link": "https://amzn.to/49Z1vsr"}
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

# --- 6. CSS LIMPO E RESPONSIVO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700;900&display=swap');
    
    /* 1. REMOÇÃO DO RODAPÉ */
    footer { visibility: hidden; display: none !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { visibility: hidden; display: none !important; }

    /* --- SUPER BANNER --- */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(240, 193, 75, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(240, 193, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(240, 193, 75, 0); }
    }
    .super-banner {
        display: block; text-decoration: none; padding: 20px; margin: 15px 0;
        position: relative; overflow: hidden; border: 1px solid rgba(128,128,128,0.2);
        animation: pulse-border 2s infinite; 
        border-radius: 8px;
    }
    .sb-badge { position: absolute; top: 0; right: 0; background: #FFD700; color: #000 !important; font-size: 0.6rem; font-weight: 900; padding: 4px 8px; }
    .sb-title { color: #FFF !important; font-weight: 900; font-size: 1.2rem; margin-bottom: 5px; display: block; text-shadow: 0px 1px 3px rgba(0,0,0,0.5); }
    .sb-prod-name { background: rgba(0,0,0,0.4); color: #FFF !important; font-size: 0.8rem; padding: 5px; margin-bottom: 15px; border-left: 3px solid #FFD700;}
    .sb-button { background: #FFF; color: #000 !important; text-align: center; font-weight: 900; padding: 12px; display: block; font-size: 0.8rem; border-radius: 4px; }

    /* --- CARD BIBLIOTECA --- */
    .lib-card {
        border: 1px solid #444; padding: 20px;
        cursor: pointer; border-left: 5px solid #F0C14B; margin-bottom: 10px;
        background-color: #262730; 
        color: white;
        border-radius: 5px;
    }
    .lib-title { font-weight: 700; color: #FFF !important; font-size: 1.1rem; margin-bottom: 8px; }
    .lib-info { color: #CCC !important; font-size: 0.8rem; display: flex; justify-content: space-between; }

    /* --- QUESTÕES & PIX --- */
    .pix-container { border: 2px dashed #888; padding: 20px; text-align: center; margin-top: 20px; border-radius: 10px;}
    .pix-key { font-family: monospace; background: #EEE; padding: 15px; color: #333 !important; font-size: 0.9rem; word-break: break-all; border: 1px solid #CCC; margin-top: 5px; font-weight: bold;}
    
    .questao-container { 
        background-color: #262730; 
        color: white !important;
        border: 1px solid #444; 
        border-left: 5px solid #666; 
        padding: 20px; margin-bottom: 30px; 
        border-radius: 8px;
    }
    .questao-texto { color: white !important; }
    
    .feedback-correct { background: #d4edda; border: 1px solid #c3e6cb; color: #155724 !important; padding: 15px; margin-top: 10px; font-weight: bold; border-radius: 5px;}
    .feedback-wrong { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24 !important; padding: 15px; margin-top: 10px; font-weight: bold; border-radius: 5px;}

</style>
""", unsafe_allow_html=True)

# --- 7. ESTADO ---
if "historico" not in st.session_state: st.session_state.historico = carregar_historico_bd()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "upload"
if "chat_ativo_id" not in st.session_state: st.session_state.chat_ativo_id = None
if "mensagens_ia" not in st.session_state: st.session_state.mensagens_ia = [{"role": "model", "content": "Olá! Sou seu Tutor IA."}]

# --- 8. FUNÇÕES DO SISTEMA ---
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
    if not API_KEY:
        st.error("⚠️ Configure a API KEY no secrets.toml")
        return None
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = """Gere um JSON estrito. Estrutura: [{"id": 1, "pergunta": "...", "opcoes": ["A) ...", "B) ..."], "correta": "A", "comentario": "..."}]"""
    if len(texto) < 500: contexto = f"Assunto: {texto}"
    else: contexto = f"Modo: {tipo}. Texto: {texto[:30000]}"
    try:
        response = model.generate_content(prompt + "\n\n" + contexto)
        limpo = response.text.replace("```json", "").replace("```", "").strip()
        if "[" in limpo: limpo = limpo[limpo.find("["):limpo.rfind("]")+1]
        return json.loads(limpo)
    except Exception as e: 
        st.error(f"Erro IA: {e}")
        return None

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

# --- 9. BARRA LATERAL (COM NAVEGAÇÃO 'ON CLICK') ---
with st.sidebar:
    st.header("PRATICA.AI 🐱")
    st.markdown("---")
    
    # Botões usando Callbacks (A chave do sucesso no Mobile)
    st.button("📄 NOVO UPLOAD", on_click=navegar, args=("upload",), use_container_width=True)
    st.button("📚 BIBLIOTECA", on_click=navegar, args=("biblioteca",), use_container_width=True)
    st.button("🤖 TUTOR IA", on_click=navegar, args=("chat_ia",), use_container_width=True)
    st.button("🐱 APOIE", on_click=navegar, args=("apoio",), use_container_width=True)
    
    st.markdown("---")
    
    # BANNER
    contexto_usuario = ""
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo: contexto_usuario = estudo_ativo['titulo']
    elif len(st.session_state.mensagens_ia) > 1:
        contexto_usuario = st.session_state.mensagens_ia[-2]['content']

    cat_nome = ia_escolher_categoria(contexto_usuario)
    cat_data = CATALOGO_PREMIUM[cat_nome]
    prod_escolhido = random.choice(cat_data["produtos"])
    visual = cat_data["visual"]

    st.markdown("<p style='font-size: 0.7rem; color: #666; font-weight: 800; letter-spacing: 1px; margin-bottom: 5px;'>PATROCINADO</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <a href="{prod_escolhido['link']}" target="_blank" class="super-banner" style="{visual['bg_style']}">
        <div class="sb-badge">{visual['badge']}</div>
        <span class="sb-icon">{visual['icone']}</span>
        <span class="sb-title">{visual['titulo']}</span>
        <div class="sb-prod-name">👉 {prod_escolhido['nome']}</div>
        <span class="sb-button" style="color: black;">{visual['btn_text']}</span>
    </a>
    """, unsafe_allow_html=True)

# --- 10. ÁREA PRINCIPAL ---

# >>> UPLOAD <<<
if st.session_state.pagina_atual == "upload":
    st.title("Estude menos, aprenda mais.")
    st.write("Suba seu PDF e deixe a IA criar sua prova.")
    
    arquivo = st.file_uploader("SELECIONE O ARQUIVO (PDF)", type="pdf")
    
    st.markdown("<br>", unsafe_allow_html=True)
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

# >>> BIBLIOTECA <<<
elif st.session_state.pagina_atual == "biblioteca":
    
    # ESTUDO ABERTO
    if st.session_state.chat_ativo_id:
        estudo_ativo = next((e for e in st.session_state.historico if e["id"] == st.session_state.chat_ativo_id), None)
        if estudo_ativo:
            if st.button("⬅ VOLTAR", use_container_width=True): st.session_state.chat_ativo_id = None; st.rerun()
            st.markdown(f"<h3 style='margin-top:10px'>{estudo_ativo['titulo']}</h3>", unsafe_allow_html=True)
            
            st.markdown("---")
            for index, q in enumerate(estudo_ativo['questoes']):
                st.markdown(f"""
                <div class="questao-container">
                    <div style="color: #CCC; font-size: 0.8rem; margin-bottom: 10px; font-weight:bold;">QUESTÃO {index + 1:02d}</div>
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
                
    # LISTA
    else:
        st.title("Minha Biblioteca")
        if not st.session_state.historico:
            st.info("Sua biblioteca está vazia. Faça um upload!")
        else:
            for i, estudo in enumerate(st.session_state.historico):
                st.markdown(f"""
                <div class="lib-card">
                    <div class="lib-title">{estudo['titulo']}</div>
                    <div class="lib-info">
                        <span>{estudo['data']}</span>
                        <span>{len(estudo['questoes'])} questões</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button("ABRIR", key=f"open_{estudo['id']}", use_container_width=True):
                        st.session_state.chat_ativo_id = estudo['id']; st.rerun()
                with c2:
                    if st.button("✕", key=f"del_{estudo['id']}", use_container_width=True):
                        deletar_estudo_bd(estudo['id'])
                        st.session_state.historico = carregar_historico_bd(); st.rerun()

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
                if API_KEY:
                    with st.spinner("..."):
                        try:
                            model = genai.GenerativeModel('gemini-flash-latest')
                            resp = model.generate_content(f"Seja didático. User: {prompt}").text
                            st.markdown(resp)
                            st.session_state.mensagens_ia.append({"role": "model", "content": resp})
                        except Exception as e: st.error(f"Erro na API: {e}")
                else: st.error("Chave API não configurada.")
    else:
        if assunto := st.chat_input("Gerar simulado sobre..."):
             with st.spinner(f"Criando: {assunto}..."):
                questoes = chamar_ia_json(assunto, "criar")
                if questoes: criar_novo_estudo(f"Simulado: {assunto}", questoes)

# >>> APOIO <<<
elif st.session_state.pagina_atual == "apoio":
    st.title("🐱 APOIE NOSSO PROJETO!!")
    st.write("Ajude a manter o servidor ligado!")
    
    pad_esq, c_base1, c_base2, pad_dir = st.columns([1, 2, 2, 1])
    
    with c_base1:
        if os.path.exists("static/gato2.jpeg"): st.image("static/gato2.jpeg", caption="A Gerente de TI analisando se você estudou hoje.", use_container_width=True)
        elif os.path.exists("gato2.jpeg"): st.image("gato2.jpeg", caption="A Gerente de TI analisando se você estudou hoje.", use_container_width=True)
    with c_base2:
        if os.path.exists("static/gato3.jpeg"): st.image("static/gato3.jpeg", caption="Esperando o Pix cair pra comprar sachê premium.", use_container_width=True)
        elif os.path.exists("gato3.jpeg"): st.image("gato3.jpeg", caption="Esperando o Pix cair pra comprar sachê premium.", use_container_width=True)

    st.markdown("<br><div class='pix-container'><p>Copie a chave aleatória:</p><div class='pix-key'>5b84b80d-c11a-4129-b897-74fb6371dfce</div></div>", unsafe_allow_html=True)