"""Gestionnaire LLM simplifié - OpenAI uniquement"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Charger les variables d'environnement depuis .env
load_dotenv()

def create_llm(temperature=0.7):
    """Crée une instance OpenAI LLM"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non trouvée dans .env - Veuillez créer un fichier .env avec votre clé API")

    return ChatOpenAI(
        model="gpt-4o",
        temperature=temperature,
        streaming=True,
        api_key=api_key
    )

