# AutoFlash - Study Flashcard Generation Using Knowledge Graphs and AI

This repository contains the implementation of **AutoFlash**, an AI-powered system that automatically generates educational flashcards by leveraging **Knowledge Graphs** (Wikidata) and **Large Language Models** (LLMs). The system transforms structured knowledge into three types of flashcards: summaries, factual statements, and multiple-choice questions, enhancing learning efficiency through adaptive content generation.

---

## Table of Contents

1. [Overview](#overview)  
2. [Project Structure](#project-structure)  
3. [Requirements](#requirements)
4. [Installation & Setup](#install)
5. [Running the Project](#running-the-project)
6. [System Workflow](#system)
7. [Evaluation](#eval)
6. [Author](#author-and-contact) 

---

## Overview

**AutoFlash** bridges semantic knowledge representation (Wikidata) with natural language generation (LLMs) to create personalized study materials. Key features:

- **Entity Expansion**: LLM identifies subtopics from user input (e.g., "DNA" → "Nucleotide," "Double Helix").

- **Wikidata Integration**: SPARQL queries fetch structured triples (subject-predicate-object) for each subtopic.

- **Flashcard Generation**: LLM refines triples into:
    - **Summary Flashcards**: Concise topic overviews.

    - **Fact Flashcards**: Key information snippets.

    - **Questions Flashcards**: Interactive questions with distractors.

- **Export**: Flashcards can be saved as PNG images for offline use.

---

## Project Structure
```
KG_Project/
├── docs/                       # Documentation
│   ├── Project_Presentation.pptx
│   ├── Project_Proposal.pdf
│   └── Project_Report.pdf
├── venv/                       # Virtual environment (generated during setup)
├── src/
│   ├── main.py                     # Execution File
│   ├── KnowledgeEngine.py          # Backend: KG/LLM integration
│   ├── UI.py                       # Streamlit frontend entry point
│   └── images/                     # HTML/CSS for flashcard styling
├── requirements.txt                # Python dependencies
├── .config/
    └── keys.json                   # API credentials (ignored in Git)
```

---

## Requirements

- **Python 1.12** 
- **Virtual Environment** (recommended)
- **API Keys**:
    - [OpenRouter](https://openrouter.ai/) (for LLM access)
    - Wikidata (requires no key)

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YourUsername/AutoFlash.git
cd AutoFlash
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Add your OpenRouter API key to keys.json:
```json
{
    "OPENROUTER_API_KEY": "your_api_key_here",
    "OPENROUTER_API_URL": "https://openrouter.ai/api/v1/chat/completions",
    "OPENROUTER_API_MODEL": "nousresearch/deephermes-3-mistral-24b-preview:free",
    "SPARQL_ENDPOINT": "https://query.wikidata.org/sparql",
    "WIKIDATA_API_URL": "https://www.wikidata.org/w/api.php"
}

```

---

## Running the Project

### Start the Streamlit Frontend
```bash
streamlit run src/main.py
```

### To test only UI (DEBUG):
On src/main.py change to mainUI(debugUI=True)
```bash
streamlit run src/main.py
```

---

## System Workflow
1. User Input: Enter a topic (e.g., "Portugal").
2. Entity Expansion: LLM extracts subtopics (e.g., "Lisbon," "Fado").
3. Wikidata Resolution: Subtopics mapped to Q-IDs via Wikidata Search API.
4. SPARQL Querying: Fetch triples (e.g., (Lisbon, capitalOf, Portugal)).
5. Content Generation: LLM converts triples into flashcards.
6. Output: Flashcards displayed in Streamlit; export as PNG.

---

## Authors
For questions or contributions, open an issue or contact the authors.
- Mariana Gouveia
- David Guilherme 
- Guilherme Prazeres
- Duarte Gonçalves

### **Institution**: Faculdade de Ciências da Universidade de Lisboa