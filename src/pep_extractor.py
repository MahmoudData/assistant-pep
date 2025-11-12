"""Extracteur simple par regex - dernière version de chaque section"""
import re
from typing import Dict

def extract_sections_from_history(messages) -> Dict[str, str]:
    """
    Parse l'historique et extrait les sections au format ### X.Y - Titre
    Garde la DERNIÈRE occurrence de chaque section (version la plus récente)
    """
    # Filtrer UNIQUEMENT les messages qui contiennent des sections formatées
    section_messages = []
    
    for msg in messages:
        if hasattr(msg, 'type') and msg.type in ['ai', 'assistant'] and hasattr(msg, 'content'):
            # Vérifier si le message contient au moins une section avec ###
            if re.search(r"###\s*\d+(?:\.\d+)*\s*-", msg.content):
                section_messages.append(msg.content)
    
    # Concaténer UNIQUEMENT les messages contenant des sections
    full_text = "\n\n".join(section_messages)
    
    sections = {}
    
    # Pattern pour capturer les sections
    pattern = r"###\s*(\d+(?:\.\d+)*)\s*-\s*[^\n]+\n\n(.*?)(?=\n###|\n---|\Z)"
    
    for match in re.finditer(pattern, full_text, re.DOTALL):
        section_id = match.group(1).strip()
        content = match.group(2).strip()
        
        if content:
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