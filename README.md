# 📄 Assistant PEP

Assistant intelligent pour la réalisation des Plans d'Exécution de Projet (PEP) utilisant l'IA.

## 🎯 Présentation

L'Assistant PEP est une application basée sur Chainlit et LangChain qui aide les chefs de projet à créer des Plans d'Exécution de Projet (PEP) structurés et complets. L'assistant utilise GPT-4 pour guider l'utilisateur à travers les différentes sections d'un PEP et génère automatiquement un document Word formaté.

### Fonctionnalités principales

- 💬 **Interface conversationnelle** : Discussion naturelle avec l'IA pour élaborer votre PEP
- 📎 **Upload de documents** : Téléchargez vos documents de référence (PDF, DOCX, TXT)
- 🧠 **Mémoire contextuelle** : L'assistant garde le contexte de la conversation grâce à LangGraph
- 📝 **Génération automatique** : Extraction des sections et génération d'un document Word final
- 🎨 **Template personnalisable** : Utilise un template Word avec des placeholders

## 🚀 Installation

### Prérequis

- Python 3.9 ou supérieur
- Clé API OpenAI

### Étapes d'installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/your-repo/assistant-pep.git
   cd assistant-pep
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   ```

   Éditez le fichier `.env` et ajoutez votre clé API OpenAI :
   ```
   OPENAI_API_KEY=sk-votre-cle-api-openai
   ```

## 🎮 Utilisation

### Lancer l'application

```bash
chainlit run chainlit_app.py
```

L'application sera accessible à l'adresse : `http://localhost:8000`

### Version Streamlit (legacy)

Si vous souhaitez utiliser l'ancienne version Streamlit :

```bash
streamlit run app.py
```

## 📖 Guide d'utilisation

1. **Démarrage**
   - Ouvrez l'application dans votre navigateur
   - L'assistant vous accueille et vous guide

2. **Upload de documents** (optionnel)
   - Cliquez sur "📎 Uploader un document"
   - Sélectionnez vos documents de référence (PDF, DOCX, TXT)
   - L'assistant pourra s'appuyer sur ces documents pour répondre avec précision

3. **Rédaction des sections**
   - Discutez avec l'assistant pour élaborer chaque section du PEP
   - L'assistant suit un format structuré avec des sections numérotées (ex: `### 1.1 - Généralités`)
   - Chaque section est délimitée par des séparateurs `---`

4. **Génération du document**
   - Une fois les sections rédigées, cliquez sur "📄 Générer le PEP"
   - L'assistant extrait les sections de la conversation
   - Un document Word est généré automatiquement
   - Téléchargez le fichier généré

## 🏗️ Architecture

```
assistant-pep/
├── chainlit_app.py          # Application principale Chainlit
├── app.py                   # Application Streamlit (legacy)
├── requirements.txt         # Dépendances Python
├── .env.example            # Template pour les variables d'environnement
├── .chainlit/
│   └── config.toml         # Configuration Chainlit
├── src/
│   ├── llm_handler.py      # Configuration OpenAI LLM
│   ├── memory_manager.py   # Gestion de la mémoire (LangGraph)
│   ├── document_processor.py  # Extraction de texte (PDF, DOCX, TXT)
│   ├── pep_extractor.py    # Extraction des sections depuis l'historique
│   ├── pep_generator.py    # Génération du document Word
│   └── system_prompt.py    # Prompt système pour l'assistant
├── templates/
│   └── PEP_type_template.docx  # Template Word avec placeholders
└── assets/
    └── parlym_logo.png     # Logo

```

## 🔧 Technologies utilisées

- **[Chainlit](https://docs.chainlit.io/)** : Framework pour interfaces conversationnelles
- **[LangChain](https://python.langchain.com/)** : Framework pour applications LLM
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** : Gestion d'état et mémoire conversationnelle
- **[OpenAI GPT-4](https://openai.com/)** : Modèle de langage
- **[python-docx](https://python-docx.readthedocs.io/)** : Génération de documents Word
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** : Extraction de texte depuis PDF

## 📝 Format des sections PEP

L'assistant génère des sections au format Markdown structuré :

```markdown
### 1.1 - Généralités

Contenu de la section...

---

### 1.2 - Justification

Contenu de la section...

---
```

Ces sections sont ensuite extraites et insérées dans le template Word aux emplacements des placeholders correspondants (ex: `{{GENERALITES}}`, `{{JUSTIFICATION}}`, etc.).

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence MIT.

## ⚠️ Notes importantes

- Assurez-vous de ne jamais commit votre fichier `.env` contenant votre clé API
- Le fichier `.gitignore` est configuré pour ignorer automatiquement les fichiers sensibles
- Pour toute question ou problème, ouvrez une issue sur GitHub