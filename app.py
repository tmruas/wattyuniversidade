import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2 
import streamlit.components.v1 as components 

# ==========================================
# 0. Ligar o "Cérebro" (Gemini)
# ==========================================
load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY") 

if CHAVE_API:
    genai.configure(api_key=CHAVE_API)
    modelo_gemini = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.error("⚠️ API Key not found!")

# ==========================================
# Funções Auxiliares
# ==========================================
def ler_pdfs_da_cadeira(nome_cadeira):
    caminho_pasta = os.path.join("documentos", nome_cadeira)
    texto_completo = ""
    if os.path.exists(caminho_pasta):
        for ficheiro in os.listdir(caminho_pasta):
            if ficheiro.endswith(".pdf"):
                caminho_ficheiro = os.path.join(caminho_pasta, ficheiro)
                try:
                    with open(caminho_ficheiro, "rb") as f:
                        leitor_pdf = PyPDF2.PdfReader(f)
                        for pagina in leitor_pdf.pages:
                            texto_extraido = pagina.extract_text()
                            if texto_extraido:
                                texto_completo += texto_extraido + "\n"
                except Exception as e:
                    st.error(f"Error reading file {ficheiro}.")
    return texto_completo

def render_mermaid(codigo_mermaid):
    codigo_limpo = codigo_mermaid.replace("```mermaid", "").replace("```", "").strip()
    html_code = f"""
    <div class="mermaid" style="display: flex; justify-content: center; font-family: sans-serif;">
        {codigo_limpo}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    components.html(html_code, height=600, scrolling=True)
    with st.expander("Show text version of the map 👀"):
        st.code(codigo_limpo)

# ==========================================
# 1. Configuração da Página e Memória
# ==========================================
st.set_page_config(page_title="Super Tutor", page_icon="🎓", layout="wide")
# Esconder o menu do Streamlit e a marca de água para um ar mais profissional
esconder_menu = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(esconder_menu, unsafe_allow_html=True)

if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# ==========================================
# 2. Menu Lateral (Sidebar)
# ==========================================
with st.sidebar:
    st.title("⚡ Watty's Menu")
    st.success("Hello! Ready to ace the semester? 🔥") 
    st.markdown("---") 
    
    grau_escolhido = st.selectbox("🎓 Academic Degree:", ["Bachelor's", "Master's"])
    
    if grau_escolhido == "Master's":
        lista_cadeiras = [
            "Entrepreneurial Finance & Venture Capital", 
            "Economics of Education", 
            "Economics of Health and Healthcare", 
            "Applied Corporate Finance"
        ]
    else:
        lista_cadeiras = [
            "Microeconomics", 
            "Macroeconomics", 
            "Principles of Management",
            "Data Analysis"
        ]
        
    cadeira_escolhida = st.selectbox("📚 Course:", lista_cadeiras)
    st.markdown("---")
    
    st.subheader("📂 Your Documents")
    pasta_docs = "documentos" 
    if os.path.exists(pasta_docs):
        ficheiros = os.listdir(pasta_docs)
        if len(ficheiros) > 0:
            st.info(f"Awesome! I found folders/files in your documents. 📚")
        else:
            st.warning("Your 'documentos' folder is empty.")
    else:
        st.error("You haven't created the 'documentos' folder yet.")
        
    st.markdown("---")
    modo = st.radio("What are we conquering today?", [
        "💬 Socratic Chat (Q&A)", 
        "🏋️ Practice (Fun Quizzes)", 
        "📖 Learn (Ninja Summaries)", 
        "🧠 Mind Maps (Visual Overview)"
    ])

# ==========================================
# 3. Área Principal (Main Area)
# ==========================================

# --- MODO 1: CHAT SOCRÁTICO ---
if modo == "💬 Socratic Chat (Q&A)":
    st.title(f"🚀 Personal Tutor: {cadeira_escolhida}")
    st.write("Stuck on a complex concept? Let's untangle it together!")
    
    for msg in st.session_state.mensagens_chat:
        st.chat_message(msg["role"]).write(msg["content"])
        
    if len(st.session_state.mensagens_chat) == 0:
        st.chat_message("assistant", avatar="🤖").write(f"Hi! ⚡ I'm Watty. How can I help you master {cadeira_escolhida} today?")

    duvida_utilizador = st.chat_input("Type your awesome question here...")
    
    if duvida_utilizador:
        st.chat_message("user").write(duvida_utilizador)
        st.session_state.mensagens_chat.append({"role": "user", "content": duvida_utilizador})
        
        instrucao_sistema = f"""
        You are Watty, a friendly university tutor for the course '{cadeira_escolhida}'.
        Your student has ADHD, so keep it concise, highly engaging, use emojis, and release dopamine!
        All your responses MUST BE IN ENGLISH.
        IMPORTANT: Use the Socratic method. NEVER give the final answer right away. Guide the student with thoughtful questions.
        The student asks: {duvida_utilizador}
        """
        with st.spinner("Thinking of a ninja response... 🧠"):
            resposta_ai = modelo_gemini.generate_content(instrucao_sistema)
            texto_resposta = resposta_ai.text
            
        st.chat_message("assistant", avatar="🤖").write(texto_resposta)
        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_resposta})

# --- MODO 2: QUIZZES (NOVA VERSÃO MASTERCLASS) ---
elif modo == "🏋️ Practice (Fun Quizzes)":
    st.title(f"🎮 Training Zone: {cadeira_escolhida}")
    st.write("Let's test your knowledge! Choose a specific topic or test the whole course.")
    
    tema_quiz = st.text_input("🎯 Specific topic to practice (Leave blank to test everything):", placeholder="E.g., Tesla Case, Human Capital...")
    
    if st.button("🎲 Launch a Practice Challenge!"):
        with st.spinner("Preparing a beautiful 5-question quiz... ⏳"):
            texto_materia = ler_pdfs_da_cadeira(cadeira_escolhida)
            if texto_materia == "":
                st.warning(f"Oops! No PDFs found in 'documentos/{cadeira_escolhida}'.")
            else:
                foco = f"Focus strictly on the topic: '{tema_quiz}'." if tema_quiz else "Cover general concepts from all the provided notes."
                
                # Instrução rigorosa para forçar a divisão entre perguntas e respostas
                instrucao_quiz = f"""
                You are a fun and enthusiastic professor. Create a 5-question quiz about {cadeira_escolhida}, based ONLY on the text below.
                {foco}
                All content MUST BE IN ENGLISH.
                
                QUIZ STRUCTURE (Exactly 5 Questions):
                - Q1: Very Easy (Multiple Choice with A, B, C, D)
                - Q2: Easy (Multiple Choice with A, B, C, D)
                - Q3: Medium (Multiple Choice with A, B, C, D)
                - Q4: Hard (Open-ended / Written answer required)
                - Q5: Very Hard (Open-ended / Written answer required)
                
                FORMATTING RULES:
                1. First, write ONLY the 5 questions. Use clear headers like "### 📝 Question 1 (Very Easy)".
                2. Use bullet points for multiple-choice options.
                3. CRITICAL RULE: After the 5th question, you MUST write EXACTLY this word on a new line:
                ===ANSWERS===
                4. Below that word, write the "Secret Answer Key" with detailed explanations for all 5 questions.
                
                STUDENT'S NOTES:
                {texto_materia}
                """
                resposta_quiz = modelo_gemini.generate_content(instrucao_quiz)
                st.snow() 
                st.success("Challenge ready! Good luck! 🍀")
                
                # O Truque Ninja do Python: Separar o texto a meio!
                if "===ANSWERS===" in resposta_quiz.text:
                    # Cortamos o texto em duas partes
                    partes = resposta_quiz.text.split("===ANSWERS===")
                    perguntas = partes[0]
                    respostas = partes[1]
                    
                    # Mostramos as perguntas normalmente
                    st.markdown(perguntas)
                    
                    # Escondemos as respostas dentro de um botão clicável!
                    with st.expander("👀 Done? Click here to reveal the Secret Answer Key!"):
                        st.markdown(respostas)
                else:
                    # Caso a IA falhe a regra do divisor, mostramos tudo junto para não perderes o quiz
                    st.markdown(resposta_quiz.text)

# --- MODO 3: RESUMOS ---
elif modo == "📖 Learn (Ninja Summaries)":
    st.title(f"🥷 Straight-to-the-Point Summaries: {cadeira_escolhida}")
    st.write("I'll read your PDFs and give you just the juice of the subject!")
    
    tema_resumo = st.text_input("Which concept or chapter do you want to master today?")
    
    if st.button("✨ Create Magic Summary"):
        if tema_resumo:
            with st.spinner(f"Devouring the {cadeira_escolhida} PDFs... 📚🤓"):
                texto_materia = ler_pdfs_da_cadeira(cadeira_escolhida)
                if texto_materia == "":
                    st.warning(f"No PDFs found in 'documentos/{cadeira_escolhida}'.")
                else:
                    instrucao_resumo = f"""
                    Create a highly engaging and structured summary about the topic: "{tema_resumo}".
                    All content MUST BE IN ENGLISH.
                    Use ONLY the information from the text below. Use headers, bullet points, and emojis.
                    
                    CRITICAL REQUIREMENT AT THE END:
                    At the very end of your response, create a section titled "📺 Explore More on YouTube".
                    Create 2 search links for this topic using this exact markdown format:
                    * [🎥 Watch Top Videos on: Name of the concept](https://www.youtube.com/results?search_query=Name+of+the+concept)
                    Replace spaces in the URL with '+' signs. DO NOT generate direct watch?v= links to avoid broken URLs.
                    
                    STUDENT'S NOTES:
                    {texto_materia}
                    """
                    resposta_resumo = modelo_gemini.generate_content(instrucao_resumo)
                    st.balloons() 
                    st.success("Summary created successfully! 🎉")
                    st.markdown(resposta_resumo.text)
        else:
            st.warning("Type the topic first! 😉")

# --- MODO 4: MAPAS MENTAIS ---
elif modo == "🧠 Mind Maps (Visual Overview)":
    st.title(f"🗺️ Visual Mind Maps: {cadeira_escolhida}")
    st.write("Visualize the subject in a structured diagram, perfect for the brain to absorb quickly.")
    
    tema_mapa = st.text_input("What major topic do you want to map out?")
    
    if st.button("🧩 Generate Visual Mind Map"):
        if tema_mapa:
            with st.spinner(f"Drawing the mental connections for '{tema_mapa}'... 🎨"):
                texto_materia = ler_pdfs_da_cadeira(cadeira_escolhida)
                if texto_materia == "":
                    st.warning(f"No PDFs found in 'documentos/{cadeira_escolhida}'.")
                else:
                    instrucao_mapa = f"""
                    You are an expert at creating visual mind maps using Mermaid.js. 
                    Based ONLY on the text below, create a simple and clean mindmap about "{tema_mapa}".
                    All content MUST BE IN ENGLISH.
                    
                    OUTPUT RULES:
                    - Output ONLY the mermaid code. Do NOT wrap it in ```mermaid ... ``` markdown, just output the raw code.
                    - Keep node names simple and avoid special characters or long sentences.
                    
                    STUDENT'S NOTES:
                    {texto_materia}
                    """
                    resposta_mapa = modelo_gemini.generate_content(instrucao_mapa)
                    
                    st.balloons() 
                    st.success("Mind Map generated successfully! 🧠✨")
                    render_mermaid(resposta_mapa.text)
        else:

            st.warning("Tell me the topic so I can organize the information! ✏️")
