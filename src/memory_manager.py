"""Gestion de la mémoire avec LangGraph - VERSION CORRIGÉE (thread-safe)"""
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from typing import Callable, Union, Optional

class ChatbotGraph:
    def __init__(self, llm, system_prompt: Union[str, Callable[[], str]]):
        """
        Initialise le chatbot avec LLM et system prompt
        
        Args:
            llm: Instance du LLM
            system_prompt: Soit un string fixe, soit une fonction qui retourne le prompt dynamiquement
        """
        self.llm = llm
        # Stocke le prompt ou la fonction
        self._system_prompt_source = system_prompt
        # Stocke le contexte des documents (sera mis à jour avant chaque appel)
        self._docs_context = ""
        self.app = self._build_graph()
    
    def set_docs_context(self, docs_context: str):
        """
        Définit le contexte des documents (thread-safe)
        Doit être appelé avant chaque stream_chat/chat
        """
        self._docs_context = docs_context
    
    def _get_system_prompt(self) -> str:
        """Récupère le system prompt (évalue la fonction si nécessaire)"""
        if callable(self._system_prompt_source):
            base_prompt = self._system_prompt_source()
        else:
            base_prompt = self._system_prompt_source
        
        # Ajouter le contexte des documents
        return base_prompt + self._docs_context
    
    def _build_graph(self):
        workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            # Récupère le prompt dynamiquement à chaque appel
            current_prompt = self._get_system_prompt()
            system_message = SystemMessage(content=current_prompt)
            
            # ✅ SOLUTION : Filtrer les anciens SystemMessage du state
            # Car le MemorySaver sauvegarde TOUT, y compris les vieux SystemMessage
            non_system_messages = [
                m for m in state["messages"] 
                if not isinstance(m, SystemMessage)
            ]
            
            # ✅ Construire la liste finale : nouveau SystemMessage + historique sans les anciens SystemMessage
            messages = [system_message] + non_system_messages
            
            response = self.llm.invoke(messages)
            return {"messages": response}
        
        workflow.add_node("model", call_model)
        workflow.add_edge(START, "model")
        
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def chat(self, user_message, thread_id="default", docs_context: Optional[str] = None):
        """
        Envoie un message au chatbot
        
        Args:
            user_message: Message de l'utilisateur
            thread_id: ID du thread de conversation
            docs_context: Contexte des documents (optionnel)
        """
        if docs_context is not None:
            self.set_docs_context(docs_context)
        
        from langchain_core.messages import HumanMessage
        result = self.app.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}}
        )
        return result["messages"][-1]
    
    def stream_chat(self, user_message, thread_id="default", docs_context: Optional[str] = None):
        """
        Version streaming du chat
        
        Args:
            user_message: Message de l'utilisateur
            thread_id: ID du thread de conversation
            docs_context: Contexte des documents (optionnel)
        """
        if docs_context is not None:
            self.set_docs_context(docs_context)
        
        from langchain_core.messages import HumanMessage
        for chunk, metadata in self.app.stream(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages"
        ):
            # Yield uniquement les chunks du contenu
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    def get_history(self, thread_id="default"):
        """
        Récupère l'historique de la conversation
        Note: Inclut aussi les SystemMessage sauvegardés par le checkpointer
        """
        state = self.app.get_state({"configurable": {"thread_id": thread_id}})
        if state and "messages" in state.values:
            return state.values["messages"]
        return []