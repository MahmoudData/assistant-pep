"""Assistant PEP - Application Streamlit simplifiée"""
import streamlit as st
import time
from pathlib import Path
from llm_handler import create_llm
from memory_manager import ChatbotGraph
from pep_extractor import extract_sections_from_history
from pep_generator import generate_pep
from system_prompt import SYSTEM_PROMPT
from document_processor import (
    extract_text_from_file,
    format_documents_context,
)

# Configuration
st.set_page_config(
    page_title="Assistant PEP",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

TEMPLATE_PATH = "PEP_type_template.docx"

def init_session_state():
    """Initialise l'état de session"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"conv_{int(time.time())}"
    if "uploaded_docs" not in st.session_state:
        st.session_state.uploaded_docs = {}

def auto_init_chatbot():
    if st.session_state.chatbot is None:
        try:
            llm = create_llm()
            
            # Passer une FONCTION qui sera appelée à chaque message
            # pour obtenir le prompt avec les documents à jour
            st.session_state.chatbot = ChatbotGraph(llm, get_full_system_prompt)
            
            return True
        except Exception as e:
            st.error(f"❌ Erreur d'initialisation: {str(e)}")
            st.info("💡 Vérifiez votre fichier .env avec OPENAI_API_KEY")
            return False
    return True

def get_full_system_prompt():
    """Construit le system prompt complet avec le contexte des documents"""
    # Vérifier que uploaded_docs existe avant de l'utiliser
    if "uploaded_docs" not in st.session_state:
        return SYSTEM_PROMPT
    docs_context = format_documents_context(st.session_state.uploaded_docs)
    return SYSTEM_PROMPT + docs_context

def clear_conversation():
    """Efface la conversation et réinitialise"""
    st.session_state.messages = []
    st.session_state.thread_id = f"conv_{int(time.time())}"
    st.rerun()

def handle_file_upload(uploaded_files):
    """Gère l'upload et l'extraction des fichiers"""
    if not uploaded_files:
        return
    
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        
        # Vérifier si déjà traité
        if filename in st.session_state.uploaded_docs:
            continue
        
        try:
            with st.spinner(f"📄 Extraction de {filename}..."):
                # Extraire le texte
                text_content = extract_text_from_file(uploaded_file)
                
                # Stocker
                st.session_state.uploaded_docs[filename] = text_content

        except Exception as e:
            st.error(f"❌ Erreur avec {filename}: {str(e)}")

def remove_document(filename):
    """Supprime un document de la liste"""
    if filename in st.session_state.uploaded_docs:
        del st.session_state.uploaded_docs[filename]
        st.rerun()

def generate_pep_document():
    """Génère le document PEP en extrayant les sections de l'historique"""
    try:
        with st.spinner("🔄 Extraction des sections et génération du PEP..."):
            # Vérifier template
            if not Path(TEMPLATE_PATH).exists():
                st.error(f"❌ Template non trouvé: {TEMPLATE_PATH}")
                st.info("💡 Placez PEP_type_template.docx à la racine")
                return
            
            # Récupérer historique
            history = st.session_state.chatbot.get_history(st.session_state.thread_id)
            
            if not history:
                st.warning("⚠️ Aucun historique de conversation.")
                return
            
            # Extraire sections avec regex
            sections_data = extract_sections_from_history(history)
            
            if not sections_data:
                st.warning("⚠️ Aucune section détectée dans l'historique.")
                st.info("💡 Assurez-vous que le bot a rédigé les sections au format === SECTION === ")
                return
            
            # Générer Word
            import tempfile
            temp_dir = tempfile.gettempdir()
            output_path = str(Path(temp_dir) / f"PEP_{st.session_state.thread_id}.docx")

            generate_pep(TEMPLATE_PATH, sections_data, output_path)

            st.success("PEP généré avec succès !")

            # Téléchargement
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le PEP",
                    data=f.read(),
                    file_name=f"PEP_{st.session_state.thread_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        import traceback
        st.exception(traceback.format_exc())

def main():
    init_session_state()
    
    if not auto_init_chatbot():
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.sidebar.image("parlym_logo.png", width='stretch')

        st.write("")

        # === SECTION UPLOAD DE DOCUMENTS ===
        st.subheader("📎 Documents de référence")
        uploaded_files = st.file_uploader(
            "Uploadez vos documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Ces documents seront utilisés comme référence par l'assistant"
        )
        # Traiter les fichiers uploadés
        if uploaded_files:
            handle_file_upload(uploaded_files)

        st.write("")

        # Instructions pour la génération du PEP
        st.caption(
            "Assurez-vous que toutes les sections nécessaires ont été discutées avec l'assistant avant de générer le PEP."
        )

        # Bouton génération
        if st.button("📄 Générer le PEP", type="primary", use_container_width=True):
            generate_pep_document()

        st.divider()

        # Nouvelle conversation
        if st.button("🗑️ Nouvelle conversation", use_container_width=True):
            clear_conversation()
    
    # Titre principal
    st.title("📄 Assistant PEP")
    st.markdown("*Assiste les chefs de projet dans la réalisation des PEP*")
    
    # Afficher l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input utilisateur
    if user_input := st.chat_input("Votre message..."):
        # Ajouter message utilisateur
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        with st.chat_message("user", avatar="👷‍♂️"):
            st.markdown(user_input)
        
        # Obtenir réponse du bot avec contexte des documents
        try:
            with st.chat_message("assistant", avatar="✨"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Streaming de la réponse
                for chunk in st.session_state.chatbot.stream_chat(
                    user_input,
                    st.session_state.thread_id
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })
        
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            import traceback
            st.exception(traceback.format_exc())

if __name__ == "__main__":
    main()