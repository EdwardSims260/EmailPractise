import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from functools import lru_cache
import time

# --- Configuration ---
load_dotenv()
st.set_page_config(
    page_title="✉️ Email Master",
    page_icon="✉️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Data Models ---
class EmailScenario:
    def __init__(self, scenario: str, prompt: str, context: str, difficulty: str):
        self.scenario = scenario
        self.prompt = prompt
        self.context = context
        self.difficulty = difficulty

class VocabularyWord:
    def __init__(self, english: str, italian: str, definition: str = "", example: str = ""):
        self.english = english
        self.italian = italian
        self.definition = definition
        self.example = example

# --- Dictionary Service ---
class DictionaryAPI:
    def __init__(self):
        self.base_url = "https://www.dictionaryapi.com/api/v3/references/learners/json/"
        self.api_key = os.getenv("MW_API_KEY")
        self.last_call = 0
        self.delay = 1.0  # Rate limiting
    
    @lru_cache(maxsize=100)
    def lookup_word(self, word: str) -> Dict:
        now = time.time()
        if now - self.last_call < self.delay:
            time.sleep(self.delay - (now - self.last_call))
        
        response = requests.get(f"{self.base_url}{word}?key={self.api_key}")
        self.last_call = time.time()
        return response.json() if response.status_code == 200 else None

# --- Core Functions ---
# Modify your load_data function to handle missing files gracefully
def load_data() -> Tuple[List[EmailScenario], List[VocabularyWord]]:
    """Load data with error handling"""
    try:
        # Use relative path that works in deployment
        scenarios_path = os.path.join(os.path.dirname(__file__), 'data/email_scenarios.json')
        vocab_path = os.path.join(os.path.dirname(__file__), 'data/vocabulary.json')
        
        scenarios = []
        if os.path.exists(scenarios_path):
            with open(scenarios_path, 'r', encoding='utf-8') as f:
                scenarios = [EmailScenario(**s) for s in json.load(f)]
        else:
            st.warning("Default scenarios loaded - missing data file")
            scenarios = [
                EmailScenario(
                    scenario="Default Scenario",
                    prompt="Write a professional email",
                    context="This is a placeholder scenario",
                    difficulty="Medium"
                )
            ]
        
        vocabulary = []
        if os.path.exists(vocab_path):
            with open(vocab_path, 'r', encoding='utf-8') as f:
                for v in json.load(f):
                    vocabulary.append(VocabularyWord(
                        english=v.get('english', ''),
                        italian=v.get('italian', ''),
                        definition=v.get('definition', ''),
                        example=v.get('example', '')
                    ))
        
        return scenarios, vocabulary
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return [], []

def save_vocabulary(word: VocabularyWord):
    """Save new words with handling for different environments"""
    try:
        if 'STREAMLIT_DEPLOYMENT' in os.environ:
            # In Streamlit Cloud, use session state instead of file
            if 'user_vocabulary' not in st.session_state:
                st.session_state.user_vocabulary = []
            
            st.session_state.user_vocabulary.append({
                "english": word.english,
                "italian": word.italian,
                "definition": word.definition,
                "example": word.example
            })
            st.success("Saved to session vocabulary!")
        else:
            # Local development - save to file
            vocab_path = os.path.join(os.path.dirname(__file__), 'data/vocabulary.json')
            data = []
            
            if os.path.exists(vocab_path):
                with open(vocab_path, 'r') as f:
                    data = json.load(f)
            
            data.append({
                "english": word.english,
                "italian": word.italian,
                "definition": word.definition,
                "example": word.example
            })
            
            with open(vocab_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            st.success("Saved to your vocabulary file!")
            
    except Exception as e:
        st.error(f"Error saving word: {e}")

# --- UI Components ---
def render_word_explorer(api: DictionaryAPI):
    st.subheader("🔍 Word Explorer")
    col1, col2 = st.columns(2)
    
    with col1:
        new_word = st.text_input("Enter English word", key="new_word")
    
    with col2:
        italian_trans = st.text_input("Italian translation", key="italian_trans")
    
    if new_word:
        with st.spinner("Checking dictionary..."):
            data = api.lookup_word(new_word.lower())
        
        if data and isinstance(data, list) and len(data) > 0:
            definition = data[0].get('shortdef', ['No definition found'])[0]
            example = f"Example: {data[0].get('examples', [{}])[0].get('t', '')}" if data[0].get('examples') else ""
            
            st.success(f"**{new_word.capitalize()}**")
            st.markdown(f"*{definition}*")
            if example:
                st.caption(example)
            
            if italian_trans:
                if st.button("💾 Save to My Vocabulary"):
                    save_vocabulary(VocabularyWord(
                        english=new_word.lower(),
                        italian=italian_trans.lower(),
                        definition=definition,
                        example=example
                    ))
                    st.success("Saved to your vocabulary!")
                    st.balloons()
        else:
            st.warning("Word not found in dictionary")

def render_vocabulary_builder(vocabulary: List[VocabularyWord]):
    st.subheader("📚 My Vocabulary")
    
    search_term = st.text_input("Search your vocabulary")
    filtered = [w for w in vocabulary if not search_term or 
               search_term.lower() in w.english or 
               search_term.lower() in w.italian]
    
    if not filtered:
        st.info("No words found. Add some using the Word Explorer!")
        return
    
    for word in filtered:
        with st.expander(f"🌐 {word.english.capitalize()} → {word.italian.capitalize()}"):
            if word.definition:
                st.markdown(f"**Definition:** {word.definition}")
            if word.example:
                st.markdown(f"**Example:** {word.example}")
            
            # Practice buttons - modified to not use rerun()
            if st.button(f"Use '{word.english}' in email", key=f"use_{word.english}"):
                if 'user_response' not in st.session_state:
                    st.session_state.user_response = ""
                st.session_state.user_response += f" {word.english}"
                # Instead of rerun, we'll let the text area update naturally
def render_email_practice(scenario: EmailScenario, vocabulary: List[VocabularyWord]):
    st.subheader("📝 Email Practice")
    st.markdown(f"**Scenario:** {scenario.scenario}")
    st.markdown(f"*{scenario.context}*")
    
    # Vocabulary help
    if st.checkbox("Show relevant vocabulary", key="show_vocab_help"):
        relevant_words = [w for w in vocabulary if w.english in scenario.context.lower()]
        if relevant_words:
            st.caption("Vocabulary that might help:")
            cols = st.columns(3)
            for i, word in enumerate(relevant_words[:6]):
                with cols[i%3]:
                    st.markdown(f"• {word.english} → {word.italian}")
    
    # Email composition
    response = st.text_area(
        "Compose your email:",
        height=300,
        placeholder="Dear [Name],\n\n...\n\nBest regards,\n[Your Name]",
        key="user_response"
    )
    
    # Smart suggestions
    if response:
        missing_elements = []
        if "dear" not in response.lower():
            missing_elements.append("greeting (e.g., 'Dear...')")
        if not any(word in response.lower() for word in ["regards", "sincerely", "best"]):
            missing_elements.append("closing (e.g., 'Best regards')")
        
        if missing_elements:
            st.warning(f"Consider adding: {', '.join(missing_elements)}")

# --- Main App ---
def main():
    st.title("✉️ Email Master")
    st.caption("Practice business emails • Build vocabulary • Improve communication")
    
    # Initialize services
    dictionary = DictionaryAPI()
    scenarios, vocabulary = load_data()
    
    # Navigation
    menu = st.sidebar.radio(
        "Menu",
        ["📧 Email Practice", "📚 Vocabulary Builder", "🔍 Word Explorer"]
    )
    
    # Page routing
    if menu == "📧 Email Practice":
        scenario = st.sidebar.selectbox(
            "Choose scenario",
            scenarios,
            format_func=lambda x: f"{x.scenario} ({x.difficulty})"
        )
        render_email_practice(scenario, vocabulary)
        
    elif menu == "📚 Vocabulary Builder":
        render_vocabulary_builder(vocabulary)
        
    elif menu == "🔍 Word Explorer":
        render_word_explorer(dictionary)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Definitions provided by Merriam-Webster's Learner's Dictionary")

if __name__ == "__main__":
    main()
