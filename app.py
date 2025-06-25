import streamlit as st
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import time

# --- Configuration ---
st.set_page_config(
    page_title="✉️ Email Master",
    page_icon="✉️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Data Models ---
@dataclass
class EmailScenario:
    scenario: str
    prompt: str
    context: str
    difficulty: str

@dataclass
class VocabularyWord:
    english: str
    italian: str
    definition: str = ""
    example: str = ""

# --- Data Management ---
class DataManager:
    @staticmethod
    def load_scenarios() -> List[EmailScenario]:
        default_scenarios = [
            EmailScenario(
                scenario="Job Application Follow-up",
                prompt="Write a polite follow-up email after a job interview",
                context="You had an interview 5 days ago and want to check on the status",
                difficulty="Medium"
            )
        ]
        
        try:
            scenarios_path = Path(__file__).parent / "data" / "email_scenarios.json"
            if scenarios_path.exists():
                with open(scenarios_path, "r", encoding="utf-8") as f:
                    return [EmailScenario(**s) for s in json.load(f)]
            return default_scenarios
        except Exception:
            return default_scenarios

    @staticmethod
    def load_vocabulary() -> List[VocabularyWord]:
        try:
            vocab_path = Path(__file__).parent / "data" / "vocabulary.json"
            if vocab_path.exists():
                with open(vocab_path, "r", encoding="utf-8") as f:
                    return [VocabularyWord(**v) for v in json.load(f)]
            return []
        except Exception:
            return []

    @staticmethod
    def save_vocabulary(word: VocabularyWord) -> bool:
        try:
            vocab_path = Path(__file__).parent / "data" / "vocabulary.json"
            vocabulary = DataManager.load_vocabulary()
            vocabulary.append(word)
            
            with open(vocab_path, "w", encoding="utf-8") as f:
                json.dump([vars(v) for v in vocabulary], f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

# --- Core Components ---
class EmailPractice:
    @staticmethod
    def render(scenario: EmailScenario, vocabulary: List[VocabularyWord]):
        st.subheader("📝 Email Practice")
        st.markdown(f"**Scenario:** {scenario.scenario}")
        st.markdown(f"*{scenario.context}*")
        
        # Initialize session state
        if "email_response" not in st.session_state:
            st.session_state.email_response = ""
        
        # Vocabulary assistant
        EmailPractice._render_vocabulary_assistant(scenario, vocabulary)
        
        # Email composition
        response = st.text_area(
            "Compose your email:",
            value=st.session_state.email_response,
            height=300,
            placeholder="Dear [Name],\n\n...\n\nBest regards,\n[Your Name]",
            key="email_composition"
        )
        st.session_state.email_response = response
        
        # Action buttons
        EmailPractice._render_action_buttons(response)
        
        # Email analysis
        EmailPractice._render_email_analysis(response)

    @staticmethod
    def _render_vocabulary_assistant(scenario: EmailScenario, vocabulary: List[VocabularyWord]):
        if st.checkbox("💡 Show vocabulary suggestions"):
            relevant_words = [
                w for w in vocabulary 
                if w.english.lower() in scenario.context.lower()
            ][:6]  # Limit to 6 words
            
            if relevant_words:
                st.caption("Suggested vocabulary:")
                cols = st.columns(3)
                for i, word in enumerate(relevant_words):
                    with cols[i % 3]:
                        if st.button(
                            f"{word.english} → {word.italian}",
                            help=f"Definition: {word.definition}",
                            key=f"vocab_{word.english}_{i}"
                        ):
                            st.session_state.email_response += f" {word.english}"
                            st.rerun()

    @staticmethod
    def _render_action_buttons(response: str):
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✉️ Submit", type="primary"):
                if len(response.strip()) < 20:
                    st.error("Email too short (min 20 characters)")
                else:
                    st.success("Email submitted successfully!")
                    st.balloons()
        
        with col2:
            if st.button("🔄 Clear"):
                st.session_state.email_response = ""
                st.rerun()
        
        with col3:
            if st.button("📋 Insert Template"):
                st.session_state.email_response = """Dear [Recipient],

I hope this message finds you well. 

[Main content]

Best regards,
[Your Name]"""
                st.rerun()

    @staticmethod
    def _render_email_analysis(response: str):
        if not response.strip():
            return
            
        with st.expander("📊 Email Analysis", expanded=True):
            word_count = len(response.split())
            sentence_count = len([s for s in response.split('.') if len(s.strip()) > 0])
            
            st.metric("Word Count", word_count)
            st.metric("Sentences", sentence_count)
            
            # Structure check
            structure = {
                "Greeting": "dear" in response.lower(),
                "Closing": any(w in response.lower() for w in ["regards", "sincerely", "best", "cheers"]),
                "Polite": any(w in response.lower() for w in ["please", "thank you", "appreciate"])
            }
            
            st.caption("Structure Check:")
            for element, present in structure.items():
                st.write(f"{'✅' if present else '❌'} {element}")

class VocabularyManager:
    @staticmethod
    def render(vocabulary: List[VocabularyWord]):
        st.subheader("📚 My Vocabulary")
        
        search_term = st.text_input("🔍 Search vocabulary")
        filtered = [
            w for w in vocabulary 
            if not search_term or 
            search_term.lower() in w.english.lower() or 
            search_term.lower() in w.italian.lower()
        ]
        
        if not filtered:
            st.info("No words found. Add some using the Word Explorer!")
            return
        
        for word in filtered:
            with st.expander(f"🌐 {word.english.capitalize()} → {word.italian.capitalize()}"):
                st.caption(f"Definition: {word.definition}")
                if word.example:
                    st.caption(f"Example: {word.example}")
                
                if st.button(
                    f"Use '{word.english}'", 
                    key=f"use_{word.english}",
                    help="Add to email"
                ):
                    if "email_response" in st.session_state:
                        st.session_state.email_response += f" {word.english}"

# --- Main App ---
def main():
    st.title("✉️ Email Master")
    st.caption("Practice business emails • Build vocabulary • Improve communication")
    
    # Load data
    scenarios = DataManager.load_scenarios()
    vocabulary = DataManager.load_vocabulary()
    
    # Navigation
    menu = st.sidebar.radio(
        "Menu",
        ["📧 Email Practice", "📚 Vocabulary Builder"]
    )
    
    # Page routing
    if menu == "📧 Email Practice":
        scenario = st.sidebar.selectbox(
            "Choose scenario",
            scenarios,
            format_func=lambda x: f"{x.scenario} ({x.difficulty})",
            key="scenario_select"
        )
        EmailPractice.render(scenario, vocabulary)
    else:
        VocabularyManager.render(vocabulary)

if __name__ == "__main__":
    main()
