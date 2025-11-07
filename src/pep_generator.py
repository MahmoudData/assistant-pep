"""Générateur de document Word PEP - Version simplifiée"""
from docx import Document
from pathlib import Path

# Mapping section_id → placeholder dans le template Word
SECTION_TO_PLACEHOLDER = {
    "1.1": "{{GENERALITES}}",
    "1.2": "{{JUSTIFICATION}}",
    "1.3": "{{ASPECT_CONTRACTUEL}}",
    "1.4.1": "{{SCOPE_PROJET}}",
    "1.4.2": "{{BASE_DESIGN}}",
    "1.4.3": "{{CONTRAINTES_PRINCIPALES}}",
    "1.4.4": "{{DESCRIPTION_DETAILLEE_INSTALLATIONS_ET_SOLUTIONS_RETENUES}}",
    "1.4.5": "{{POINTS_EN_ATTENTE}}",
    "2": "{{ORGANISATION_EQUIPE_PROJET}}",
    "3.1": "{{DOCUMENTS_CLIENT_DE_REFERENCE}}",
    "3.2.1": "{{DOCUMENTS_CONTRACTUELS}}",
    "3.2.2": "{{DOCUMENTS_REFERENCE}}",
    "3.3": "{{DOCUMENTS_INTERNES}}",
    "4.1": "{{ORGANISATION_GENERALE}}",
    "4.2": "{{MATRICE_RESPONSABILITES}}",
    "4.3": "{{JALONS_PRINCIPAUX}}",
    "4.4": "{{REUNIONS}}",
    "4.5.1": "{{AVANCEMENT_PHYSIQUE}}",
    "4.5.2": "{{PLANNING}}",
    "4.5.3": "{{CONTROLE_COUTS}}",
    "4.5.4": "{{RISK_MANAGEMENT}}",
    "4.6": "{{REPORTING}}",
    "4.7": "{{GESTION_SCOPE_ET_MODIFICATIONS}}",
    "4.8": "{{COMMUNICATIONS}}",
    "4.9": "{{GESTION_DE_DOCUMENTATION}}",
    "5": "{{CERTIFICATION_BUREAU_DE_CONTROLE}}",
    "5.1": "{{ACTIVITES_ET_DONNEES_STRATEGIQUES}}",
    "5.2": "{{LISTE_DE_LIVRABLES_ET_ACTIVITES_REPARTITION_DES_ROLES_ET_RESPONSABILITES}}",
    "5.3": "{{EXCLUSIONS}}",
    "5.4": "{{INTERFACES_ET_LIMITES_DES_PRESTATIONS}}",
    "5.5": "{{BATTERRIE_LIMITES_TECHNIQUES}}",
    "5.6": "{{INTERFACE_DANS_ROLES_ET_REPONSABILITES}}",
    "5.7": "{{PLANNING_DES_ETUDES}}",
    "5.8": "{{MAQUETTE_3D_CAD_OUTILS_ET_LOGICIELS}}",
    "5.9": "{{RISQUES_INGENIERIE_IDENTIFIES_ET_PLAN_DE_MIGRATION}}",
    "5.10": "{{PLAN_DE_VERIFICATION_DES_ETUDES}}",
    "5.11": "{{PLAN_DE_REVUES_INGENIERIE}}",
    "6": "{{APPROVISONNEMENTS_PROCUREMENT}}",
    "6.1": "{{TUYAUTERIES}}",
    "6.2": "{{INSTRUMENTATIONS}}",
    "6.3": "{{AUTOMATISATISMES_SECURITE}}",
    "6.4": "{{MECANIQUES_ET_EQUIPEMENTS}}",
    "6.5": "{{ELECTRICITE}}",
    "6.6": "{{GENIE_CIVIL_STRUCTURE}}",
    "6.7": "{{EXPEDITING_ET_RECEPTION_MATERIEL}}",
    "6.7.1": "{{RECEPTION_DU_MATERIEL}}",
    "6.7.2": "{{FACTORY_ACCEPTANCE_TEST}}",
    "6.7.3": "{{SITE_ACCEPTANCE_TEST}}",
    "6.7.4": "{{TEST_DE_PERFORMANCE_GARANTIES}}",
    "7": "{{MARCHES_DE_TRAVAUX}}",
    "8.1": "{{CONSTRUCTION_GENERALITES}}",
    "8.2": "{{INSTALLATIONS_TEMPORAIRES}}",
    "8.3": "{{HSE_CHANTIER}}",
    "8.4": "{{PIPING_CALO_ECHAFAUDAGES}}",
    "8.5": "{{EIA}}",
    "8.7": "{{PROCESS_CONTROL_AUTOMATISME}}",
    "8.8": "{{AUTRES_LEVERAGE_LOURD_MONTAGE_MECANIQUE}}",
    "8.9": "{{MISES_A_DISPOSITIONS}}",
    "8.10": "{{QUALITES_DES_TRAVAUX}}",
    "8.11": "{{CONSIGNATIONS_ET_DECONSIGNATIONS}}",
    "8.12": "{{MECHANICAL_COMPLETION}}",
    "10": "{{PRECOM_COMMISSIONING_MISE_EN_SERVICE}}",
    "11": "{{PIECES_DE_RECHANGES}}",
    "12": "{{DESAFFECTION_DU_MATERIEL}}",
    "13": "{{FORMATIONS_DU_PERSONNEL_CLIENT}}",
    "14": "{{AUTORISATION_EXPLOITER_PERMIS_DE_CONSTRUIRE}}",
}


def replace_in_paragraph(paragraph, replacements: dict):
    """
    Remplace les placeholders dans un paragraphe
    
    Args:
        paragraph: Objet paragraph de python-docx
        replacements: Dict {placeholder: valeur}
    """
    # Remplacement qui conserve le style d'origine (runs)
    for placeholder, value in replacements.items():
        for run in paragraph.runs:
            if placeholder in run.text:
                replacement = value if value and value.strip() else "[À compléter]"
                run.text = run.text.replace(placeholder, replacement)


def generate_pep(template_path: str, sections_data: dict, output_path: str):
    """
    Génère le document PEP en remplaçant les placeholders
    
    Args:
        template_path: Chemin du template Word
        sections_data: Dict {section_id: content} ex: {"1.1": "Texte...", "1.2": "..."}
        output_path: Chemin de sortie du document
    
    Returns:
        True si succès, False sinon
    """
    if not Path(template_path).exists():
        raise FileNotFoundError(f"❌ Template non trouvé: {template_path}")
    
    # Construire le dict de remplacement {placeholder → valeur}
    replacements = {}
    for section_id, content in sections_data.items():
        placeholder = SECTION_TO_PLACEHOLDER.get(section_id)
        if placeholder:
            replacements[placeholder] = content
    
    # Charger le document
    doc = Document(template_path)
    
    # Remplacer dans tous les paragraphes du document
    for paragraph in doc.paragraphs:
        replace_in_paragraph(paragraph, replacements)
    
    # Remplacer dans tous les tableaux
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_in_paragraph(paragraph, replacements)
    
    # Sauvegarder
    doc.save(output_path)
    return True