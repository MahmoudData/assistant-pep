"""Application Chainlit pour l'Assistant PEP - Version simplifiée avec LangGraph"""
import chainlit as cl
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.memory import MemorySaver
from pathlib import Path
import tempfile
import time

from src.document_processor import extract_text_from_file, format_documents_context
from src.pep_extractor import extract_sections_from_history
from src.pep_generator import generate_pep
from src.system_prompt import SYSTEM_PROMPT
from dotenv import load_dotenv

# Configuration
TEMPLATE_PATH = "templates/PEP_type_template.docx"

# Définir les commandes disponibles
COMMANDS = [
    {
        "id": "generate_pep",
        "icon": "file-text",
        "description": "Générer le PEP final au format Word"
    }
]

# Charge les variables d'environnement
load_dotenv()

def create_graph():
    """
    Crée le graph LangGraph simple avec un seul node pour le modèle
    """
    def call_model(state: MessagesState):
        # Récupérer le contexte des documents depuis user_session
        docs_context = cl.user_session.get("docs_context", "")
        
        # Créer le system message avec le prompt + contexte docs
        system_msg = SystemMessage(content=SYSTEM_PROMPT + docs_context)
        
        # LLM avec streaming activé
        llm = ChatOpenAI(
            model="gpt-4o",
            streaming=True,
            temperature=0.7,
        )

        # Construire les messages : system + historique
        messages = [system_msg] + state["messages"]
        
        # Invoquer le LLM
        response = llm.invoke(messages)
        
        return {"messages": [response]}
    
    # Construire le graph
    workflow = StateGraph(MessagesState)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")
    
    # Compiler avec memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


@cl.set_starters
async def set_starters():
    """
    Définit les messages de démarrage cliquables
    """
    return [
        cl.Starter(
            label="Commençons",
            message="Commençons"
        )
    ]


@cl.on_chat_start
async def start():
    """
    Initialise la session de chat
    """
    # 1. Définir les commandes disponibles
    await cl.context.emitter.set_commands(COMMANDS)

    # 2. Créer le graph LangGraph
    graph = create_graph()

    # 3. Initialiser le stockage dans user_session
    cl.user_session.set("graph", graph)
    cl.user_session.set("docs_context", "")
    cl.user_session.set("uploaded_docs", {})
    



@cl.on_message
async def main(msg: cl.Message):
    """
    Traite les messages utilisateur et les commandes
    """
    # === CAS 1: Commande /generate_pep ===
    if msg.command == "generate_pep":
        await generate_pep_document()
        return
    
    # === CAS 2: Upload de fichiers ===
    if msg.elements:
        await process_uploaded_files(msg.elements)
        # Ne pas retourner, on traite aussi le message texte si présent
    
    # === CAS 3: Message de chat normal ===
    graph = cl.user_session.get("graph")
    
    # Configuration avec thread_id unique par session
    config = {"configurable": {"thread_id": cl.context.session.id}}
    
    # Créer un message vide pour le streaming
    response_msg = cl.Message(content="")
    
    # Streaming avec astream_events
    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=msg.content)]},
            config=config,
            version="v2"
        ):
            kind = event["event"]
            
            # Filtrer uniquement les tokens du modèle
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    await response_msg.stream_token(content)
        
        # Envoyer le message complet
        await response_msg.send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ Erreur lors du traitement : {str(e)}"
        ).send()


async def process_uploaded_files(files):
    """
    Traite les fichiers uploadés et les stocke dans user_session
    """
    uploaded_docs = cl.user_session.get("uploaded_docs", {})
    
    new_files = []
    for file in files:
        filename = file.name
        
        # Vérifier si déjà uploadé
        if filename in uploaded_docs:
            continue
        
        try:
            # Extraire le texte
            text_content = extract_text_from_file(file)
            uploaded_docs[filename] = text_content
            new_files.append(filename)
            
        except Exception as e:
            await cl.Message(
                content=f"❌ Erreur avec {filename}: {str(e)}"
            ).send()
    
    # Mettre à jour le contexte des documents
    if new_files:
        docs_context = format_documents_context(uploaded_docs)
        cl.user_session.set("docs_context", docs_context)
        cl.user_session.set("uploaded_docs", uploaded_docs)
        
        files_list = "\n".join([f"- {name}" for name in new_files])
        await cl.Message(
            content=f"✅ **Documents chargés avec succès :**\n{files_list}"
        ).send()


async def generate_pep_document():
    """
    Génère le document PEP Word à partir de l'historique
    """
    try:
        # 1. Récupérer le graph et l'état
        graph = cl.user_session.get("graph")
        config = {"configurable": {"thread_id": cl.context.session.id}}
        
        state = graph.get_state(config)
        history = state.values.get("messages", [])
        
        if not history:
            await cl.Message(
                content="⚠️ Aucun historique de conversation. Veuillez d'abord échanger avec l'assistant pour remplir les sections du PEP."
            ).send()
            return
        
        # 2. Extraire les sections avec regex
        #await cl.Message(content="🔄 Extraction des sections de l'historique...").send()
        sections_data = extract_sections_from_history(history)
        
        if not sections_data:
            await cl.Message(
                content="""⚠️ **Aucune section détectée dans l'historique.**

💡 **Astuce :** Les sections doivent être rédigées au format suivant :

```
### X.Y - Titre de la section

Contenu de la section...
---
```

Continuez la conversation avec l'assistant pour remplir les sections, puis réessayez la génération."""
            ).send()
            return
        
        # 3. Vérifier que le template existe
        if not Path(TEMPLATE_PATH).exists():
            await cl.Message(
                content=f"❌ **Template non trouvé :** `{TEMPLATE_PATH}`\n\n💡 Assurez-vous que le fichier `PEP_type_template.docx` est présent dans le dossier `templates/`"
            ).send()
            return
        
        # 4. Générer le document Word
        #await cl.Message(content="📝 Génération du document Word...").send()
        
        output_path = Path(tempfile.gettempdir()) / f"PEP_{int(time.time())}.docx"
        generate_pep(TEMPLATE_PATH, sections_data, str(output_path))
        
        # 5. Envoyer le fichier pour téléchargement
        sections_count = len(sections_data)
        sections_list = ", ".join(sorted(sections_data.keys(), key=lambda x: [int(n) for n in x.split('.')]))
        
        await cl.Message(
            content=f"""✅ **PEP généré avec succès !**
📥 Cliquez sur le fichier ci-dessous pour télécharger votre PEP.""",
            elements=[
                cl.File(
                    name="PEP_generated.docx",
                    path=str(output_path),
                    display="inline"
                )
            ]
        ).send()
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        await cl.Message(
            content=f"""❌ **Erreur lors de la génération du PEP**

```
{str(e)}
```

Détails techniques :
```
{error_detail}
```"""
        ).send()


# Point d'entrée pour le debug
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)