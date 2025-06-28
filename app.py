import streamlit as st
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import time
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# --- Configuration ---
st.set_page_config(
    page_title="EDWARD.png Learn With Edward",
    page_icon="EDWARD.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

def add_bg_from_local(image_file): 
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: 300px;
            background-repeat: no-repeat;
            background-position: right bottom;
            background-attachment: fixed;
            background-opacity: 0.1;
        }}
        </style>
        """,
        unsafe_allow_html=True
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
            ),
            EmailScenario(
                scenario="Client Complaint Response",
                prompt="Respond professionally to a dissatisfied client",
                context="A client is unhappy with delayed delivery of your service",
                difficulty="Hard"
            ),
            EmailScenario(
                scenario="Meeting Request",
                prompt="Request a meeting with a potential business partner",
                context="You want to discuss a possible collaboration next week",
                difficulty="Easy"
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
        EmailPractice._render_email_analysis(response, scenario)

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
    def _render_email_analysis(response: str, scenario: EmailScenario):
        if not response.strip():
            return
            
        with st.expander("📊 Detailed Email Analysis", expanded=True):
            # Basic metrics
            word_count = len(response.split())
            sentence_count = len([s for s in response.split('.') if len(s.strip()) > 0])
            paragraph_count = len([p for p in response.split('\n\n') if len(p.strip()) > 0])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Word Count", word_count)
            col2.metric("Sentences", sentence_count)
            col3.metric("Paragraphs", paragraph_count)
            
            # Structure analysis
            st.subheader("Structure Analysis")
            structure = {
                "Greeting": ("dear" in response.lower(), "Should include a proper greeting (e.g., 'Dear [Name]')"),
                "Closing": (any(w in response.lower() for w in ["regards", "sincerely", "best", "cheers", "cordially"]), 
                          "Should include a proper closing (e.g., 'Best regards')"),
                "Polite Language": (any(w in response.lower() for w in ["please", "thank you", "appreciate", "grateful"]), 
                                  "Should include polite phrases"),
                "Clear Purpose": (any(w in response.lower() for w in ["purpose", "reason", "writing", "contacting"] + scenario.prompt.lower().split()),
                                "Should clearly state the purpose of the email"),
                "Professional Tone": (not any(w in response.lower() for w in ["hey", "hi", "what's up", "lol"]),
                                   "Should maintain professional tone")
            }
            
            for element, (present, feedback) in structure.items():
                if present:
                    st.success(f"✅ {element}: {feedback}")
                else:
                    st.error(f"❌ {element}: {feedback}")
            
            # Grammar and style suggestions
            st.subheader("Language & Style Suggestions")
            
            # Check for common mistakes
            common_mistakes = {
                "Passive voice": ["was done", "were given", "is being", "has been"],
                "Long sentences": [s for s in response.split('.') if len(s.split()) > 25],
                "Complex words": ["utilize", "endeavor", "fabricate", "elucidate"],
                "Contractions": ["don't", "can't", "won't", "isn't"],
                "Weak phrases": ["I think", "just", "maybe", "perhaps", "a bit"]
            }
            
            for mistake_type, indicators in common_mistakes.items():
                found = False
                details = []
                
                if mistake_type == "Long sentences":
                    for i, sentence in enumerate(indicators):
                        if sentence.strip():
                            details.append(f"Sentence {i+1}: '{sentence.strip()[:50]}...'")
                    found = bool(details)
                else:
                    for phrase in indicators:
                        if phrase.lower() in response.lower():
                            found = True
                            details.append(f"Found: '{phrase}'")
                
                if found:
                    st.warning(f"⚠️ {mistake_type}:")
                    for detail in details:
                        st.text(detail)
            
            # Generate highlighted text with mistakes
            st.subheader("Highlighted Text Analysis")
            highlighted_html = EmailPractice._highlight_text(response, scenario)
            st.markdown(highlighted_html, unsafe_allow_html=True)
            
            # Download button for analysis
            EmailPractice._generate_analysis_image(response, scenario)

    @staticmethod
    def _highlight_text(text: str, scenario: EmailScenario) -> str:
        # Define color coding for different issues
        highlight_rules = [
            (r"\b(dear)\b", "#4CAF50", "Greeting"),  # Green for good
            (r"\b(regards|sincerely|best|cheers|cordially)\b", "#4CAF50", "Closing"),
            (r"\b(please|thank you|appreciate|grateful)\b", "#4CAF50", "Polite"),
            (r"\b(hey|hi|what's up|lol)\b", "#FF5252", "Informal"),  # Red for bad
            (r"\b(just|maybe|perhaps|a bit)\b", "#FF9800", "Weak phrase"),  # Orange
            (r"\b(utilize|endeavor|fabricate|elucidate)\b", "#9C27B0", "Complex word"),  # Purple
            (r"\b(don't|can't|won't|isn't)\b", "#2196F3", "Contraction"),  # Blue
            (r"\b(I think|I believe|in my opinion)\b", "#FFC107", "Hesitation")  # Yellow
        ]
        
        # Add scenario-specific keywords
        for word in scenario.prompt.lower().split() + scenario.context.lower().split():
            if len(word) > 4:  # Avoid short words
                highlight_rules.append((fr"\b({word})\b", "#00BCD4", "Scenario keyword"))
        
        # Apply highlighting
        highlighted = text
        for pattern, color, title in highlight_rules:
            highlighted = re.sub(
                pattern, 
                f'<span style="background-color: {color}; border-radius: 3px; padding: 0 2px;" title="{title}">\\1</span>', 
                highlighted, 
                flags=re.IGNORECASE
            )
        
        return f'<div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap;">{highlighted}</div>'

    @staticmethod
    def _generate_analysis_image(text: str, scenario: EmailScenario):
        # Create an image with analysis
        img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # Use a default font (size may vary by system)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
            title_font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Add title
        d.text((50, 50), f"Email Analysis: {scenario.scenario}", font=title_font, fill=(0, 0, 0))
        
        # Add watermark
        d.text((600, 1150), "www.learnwithedward.com", font=font, fill=(200, 200, 200))
        
        # Add analysis content
        y_position = 100
        analysis_lines = [
            "Email Content:",
            text,
            "",
            "Analysis Summary:",
            f"- Scenario: {scenario.scenario}",
            f"- Word Count: {len(text.split())}",
            f"- Sentences: {len([s for s in text.split('.') if len(s.strip()) > 0])}",
            "",
            "Key Recommendations:",
            "1. Use clear, concise language",
            "2. Maintain professional tone",
            "3. State purpose early in email",
            "4. Include polite closing",
            "5. Avoid contractions in formal emails"
        ]
        
        for line in analysis_lines:
            d.text((50, y_position), line, font=font, fill=(0, 0, 0))
            y_position += 30
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Download button
        st.download_button(
            label="📥 Download Analysis Report",
            data=img_byte_arr,
            file_name=f"email_analysis_{scenario.scenario[:20]}.png",
            mime="image/png"
        )

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
    # Set app title and background
    st.title("✉️ Learn With Edward")
    st.caption("Practice business emails • Build vocabulary • Improve communication")
    
    # Add background logo (replace with your actual logo path)
    try:
        add_bg_from_local("EDWARD.png")  # Replace with your logo path
    except:
        st.warning("Logo image not found - running without background")
    
    # Load data
    scenarios = DataManager.load_scenarios()
    vocabulary = DataManager.load_vocabulary()
    
    # Navigation
    menu = st.sidebar.radio(
        "Menu",
        ["📧 Email Practice", "📚 Vocabulary Builder"],
        horizontal=True
    )
    
    # Add sidebar branding
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Learn With Edward")
    st.sidebar.markdown("Improve your business communication skills")
    st.sidebar.markdown("[www.learnwithedward.com](https://www.learnwithedward.com)")
    
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
