"""Gestionnaire LLM simplifié - OpenAI uniquement"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import streamlit as st

def create_llm(temperature=0.7):
    """Crée une instance OpenAI LLM"""
    api_key = st.secrets("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non trouvée dans .env")
    
    return ChatOpenAI(
        model="gpt-4.1",
        streaming=True,
        api_key=api_key
    )

