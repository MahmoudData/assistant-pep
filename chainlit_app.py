"""Assistant PEP - Application Chainlit"""
import chainlit as cl
import time
from pathlib import Path
from src.llm_handler import create_llm
from src.memory_manager import ChatbotGraph
from src.pep_extractor import extract_sections_from_history
from src.pep_generator import generate_pep
from src.system_prompt import SYSTEM_PROMPT
from src.document_processor import (
    extract_text_from_file,
    format_documents_context,
)
import tempfile
import os

TEMPLATE_PATH = "templates/PEP_type_template.docx"


@cl.on_chat_start
async def on_chat_start():
    """Initialise la session au démarrage du chat"""

    # Afficher le logo et message de bienvenue
    await cl.Message(
        content="# 📄 Assistant PEP\n*Assiste les chefs de projet dans la réalisation des PEP*\n\nBonjour! Je suis votre assistant pour créer des Plans d'Exécution de Projet (PEP). Je peux vous aider à structurer et rédiger votre PEP selon les bonnes pratiques.\n\n**Pour commencer:**\n1. Uploadez vos documents de référence si nécessaire (PDF, DOCX, TXT)\n2. Posez-moi vos questions ou demandez-moi de rédiger des sections du PEP\n3. Une fois les sections rédigées, générez le document Word final",
        author="Assistant"
    ).send()

    # Initialiser le chatbot
    try:
        llm = create_llm()
        chatbot = ChatbotGraph(llm, SYSTEM_PROMPT)

        # Stocker dans la session
        cl.user_session.set("chatbot", chatbot)
        cl.user_session.set("thread_id", f"conv_{int(time.time())}")
        cl.user_session.set("uploaded_docs", {})

        # Créer les actions pour upload et génération PEP
        actions = [
            cl.Action(
                name="upload_document",
                value="upload",
                label="📎 Uploader un document",
                description="Uploader un document de référence (PDF, DOCX, TXT)"
            ),
            cl.Action(
                name="generate_pep",
                value="generate",
                label="📄 Générer le PEP",
                description="Générer le document Word PEP à partir de la conversation"
            ),
            cl.Action(
                name="clear_conversation",
                value="clear",
                label="🗑️ Nouvelle conversation",
                description="Recommencer une nouvelle conversation"
            )
        ]

        await cl.Message(
            content="✅ Assistant initialisé avec succès! Vous pouvez maintenant commencer à discuter.",
            actions=actions
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ Erreur d'initialisation: {str(e)}\n\n💡 Vérifiez votre fichier .env avec OPENAI_API_KEY",
            author="System"
        ).send()


@cl.action_callback("upload_document")
async def on_upload_document(action: cl.Action):
    """Gère l'upload de documents"""
    files = await cl.AskFileMessage(
        content="📎 Uploadez vos documents de référence (PDF, DOCX, TXT)",
        accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        max_files=10,
        max_size_mb=20
    ).send()

    if not files:
        await cl.Message(content="⚠️ Aucun fichier uploadé.").send()
        return

    uploaded_docs = cl.user_session.get("uploaded_docs", {})

    for file in files:
        filename = file.name

        # Créer un objet file-like pour l'extraction
        class FileWrapper:
            def __init__(self, path, mime_type):
                self.path = path
                self.type = mime_type
                self._content = None

            def read(self):
                if self._content is None:
                    with open(self.path, 'rb') as f:
                        self._content = f.read()
                return self._content

            def seek(self, pos):
                pass  # Not needed for our use case

        try:
            file_wrapper = FileWrapper(file.path, file.mime)
            text_content = extract_text_from_file(file_wrapper)
            uploaded_docs[filename] = text_content

            await cl.Message(
                content=f"✅ Document **{filename}** chargé avec succès ({len(text_content)} caractères extraits)"
            ).send()

        except Exception as e:
            await cl.Message(content=f"❌ Erreur avec {filename}: {str(e)}").send()

    cl.user_session.set("uploaded_docs", uploaded_docs)

    # Afficher la liste des documents chargés
    if uploaded_docs:
        docs_list = "\n".join([f"• {name}" for name in uploaded_docs.keys()])
        await cl.Message(
            content=f"📚 **Documents de référence chargés:**\n{docs_list}"
        ).send()


@cl.action_callback("generate_pep")
async def on_generate_pep(action: cl.Action):
    """Génère le document PEP"""
    chatbot = cl.user_session.get("chatbot")
    thread_id = cl.user_session.get("thread_id")

    if not chatbot:
        await cl.Message(content="❌ Chatbot non initialisé.").send()
        return

    try:
        msg = cl.Message(content="🔄 Extraction des sections et génération du PEP...")
        await msg.send()

        # Vérifier template
        if not Path(TEMPLATE_PATH).exists():
            await cl.Message(
                content=f"❌ Template non trouvé: {TEMPLATE_PATH}\n\n💡 Placez PEP_type_template.docx dans le dossier templates/"
            ).send()
            return

        # Récupérer historique
        history = chatbot.get_history(thread_id)

        if not history:
            await cl.Message(content="⚠️ Aucun historique de conversation.").send()
            return

        # Extraire sections avec regex
        sections_data = extract_sections_from_history(history)

        if not sections_data:
            await cl.Message(
                content="⚠️ Aucune section détectée dans l'historique.\n\n💡 Assurez-vous que le bot a rédigé les sections au format:\n```\n### X.Y - TITRE\n\nContenu...\n\n---\n```"
            ).send()
            return

        # Générer Word
        temp_dir = tempfile.gettempdir()
        output_path = str(Path(temp_dir) / f"PEP_{thread_id}.docx")

        generate_pep(TEMPLATE_PATH, sections_data, output_path)

        # Envoyer le fichier
        elements = [
            cl.File(
                name=f"PEP_{thread_id}.docx",
                path=output_path,
                display="inline"
            )
        ]

        sections_count = len(sections_data)
        sections_list = ", ".join(sorted(sections_data.keys()))

        await cl.Message(
            content=f"✅ **PEP généré avec succès!**\n\n📊 **{sections_count} sections** extraites: {sections_list}\n\n📥 Téléchargez le document ci-dessous:",
            elements=elements
        ).send()

    except Exception as e:
        import traceback
        await cl.Message(
            content=f"❌ Erreur lors de la génération: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        ).send()


@cl.action_callback("clear_conversation")
async def on_clear_conversation(action: cl.Action):
    """Efface la conversation et réinitialise"""
    try:
        llm = create_llm()
        chatbot = ChatbotGraph(llm, SYSTEM_PROMPT)

        cl.user_session.set("chatbot", chatbot)
        cl.user_session.set("thread_id", f"conv_{int(time.time())}")
        cl.user_session.set("uploaded_docs", {})

        await cl.Message(
            content="🗑️ Conversation effacée. Nouvelle session démarrée!"
        ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ Erreur lors de la réinitialisation: {str(e)}"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Gère les messages de l'utilisateur"""
    chatbot = cl.user_session.get("chatbot")
    thread_id = cl.user_session.get("thread_id")
    uploaded_docs = cl.user_session.get("uploaded_docs", {})

    if not chatbot:
        await cl.Message(content="❌ Chatbot non initialisé.").send()
        return

    # Préparer le contexte des documents
    docs_context = format_documents_context(uploaded_docs) if uploaded_docs else ""

    # Créer le message de réponse avec streaming
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Stream la réponse
        full_response = ""
        async for chunk in chatbot.async_stream_chat(
            message.content,
            thread_id,
            docs_context=docs_context
        ):
            full_response += chunk
            await msg.stream_token(chunk)

        # Finaliser le message
        await msg.update()

    except Exception as e:
        import traceback
        await cl.Message(
            content=f"❌ Erreur: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        ).send()


if __name__ == "__main__":
    # Note: Pour lancer l'application, utilisez: chainlit run chainlit_app.py
    pass
