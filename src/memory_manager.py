"""Gestion de la mémoire avec LangGraph"""
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from typing import Callable, Union

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
        self.app = self._build_graph()
    
    def _get_system_prompt(self) -> str:
        """Récupère le system prompt (évalue la fonction si nécessaire)"""
        if callable(self._system_prompt_source):
            return self._system_prompt_source()
        return self._system_prompt_source
    
    def _build_graph(self):
        workflow = StateGraph(state_schema=MessagesState)
        
        def call_model(state: MessagesState):
            # Récupère le prompt dynamiquement à chaque appel
            current_prompt = self._get_system_prompt()
            system_message = SystemMessage(content=current_prompt)
            messages = [system_message] + state["messages"]
            response = self.llm.invoke(messages)
            return {"messages": response}
        
        workflow.add_node("model", call_model)
        workflow.add_edge(START, "model")
        
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def chat(self, user_message, thread_id="default"):
        from langchain_core.messages import HumanMessage
        result = self.app.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}}
        )
        return result["messages"][-1]
    
    def stream_chat(self, user_message, thread_id="default"):
        """Version streaming du chat"""
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
        state = self.app.get_state({"configurable": {"thread_id": thread_id}})
        if state and "messages" in state.values:
            return state.values["messages"]
        return []