"""Extracteur simple par regex - dernière version de chaque section"""
import re
from typing import Dict

def extract_sections_from_history(messages) -> Dict[str, str]:
    """
    Parse l'historique et extrait les sections au format === SECTION ===
    Garde la DERNIÈRE occurrence de chaque section (version la plus récente)
    
    Args:
        messages: Liste des messages de LangGraph
        
    Returns:
        Dict {section_id: content} ex: {"1.1": "Le projet...", "1.2": "..."}
    """
    # Concaténer tout l'historique de l'assistant
    full_text = "\n\n".join([
        msg.content 
        for msg in messages 
        if hasattr(msg, 'type') and msg.type in ['ai', 'assistant']
        and hasattr(msg, 'content')
    ])
    
    sections = {}  # section_id -> content
    
    # Pattern pour capturer les sections (Markdown)
    pattern = r"### (\d+(?:\.\d+)*) - ([^\n]+)\n\n(.*?)(?=\n---|\Z)"
    
    # Trouver toutes les sections (re.finditer retourne dans l'ordre chronologique)
    for match in re.finditer(pattern, full_text, re.DOTALL | re.IGNORECASE):
        section_id = match.group(1).strip()
        content = match.group(3).strip()
        # Écraser avec la dernière version (la plus récente)
        sections[section_id] = content
    
    return sections


def get_sections_summary(sections: Dict[str, str]) -> str:
    """
    Génère un résumé des sections trouvées
    
    Args:
        sections: Dict {section_id: content}
        
    Returns:
        Texte résumé pour affichage
    """
    if not sections:
        return "Aucune section détectée"
    
    summary = []
    for sec_id in sorted(sections.keys(), key=lambda x: [int(n) for n in x.split('.')]):
        content_preview = sections[sec_id][:80].replace('\n', ' ')
        summary.append(f"  • Section {sec_id}: {content_preview}...")
    
    return "\n".join(summary)