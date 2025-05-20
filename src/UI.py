from KnowledgeEngine import KnowledgeEngine
import streamlit as st
import random

# ---------- Constants ----------

POST_IT_COLORS = ["#cdfc93", "#ff7ecd", "#71d7ff", "#ce81ff", "#fff68b"]
SHARED_CARD_STYLE = """
    background: {bg_color};
    padding: 25px 20px;
    border-radius: 12px;
    max-width: 600px;
    box-shadow: 5px 7px 15px rgba(0,0,0,0.3);
    font-family: 'Comic Sans MS', cursive, sans-serif;
    border: 2px solid {border_color};
    margin-top: 20px;
    position: relative;
"""

STICKER_DECORATION = """
    content: '';
    position: absolute;
    top: 0px;
    left: -15px;
    width: 60px;
    height: 15px;
    background: repeating-linear-gradient(
        45deg,
        #FFD580,
        #FFD580 5px,
        #FFA500 5px,
        #FFA500 10px
    );
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    transform: rotate(-40deg);
"""

# ---------- Utilities ----------

def setupUI():
    st.set_page_config(page_title="KG Project", page_icon=":guardsman:", layout="centered")

def darker_color(hex_color, amount=30):
    hex_color = hex_color.lstrip('#')
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    r, g, b = max(r - amount, 0), max(g - amount, 0), max(b - amount, 0)
    return f"#{r:02x}{g:02x}{b:02x}"

def initialize_state():
    st.session_state.setdefault('active_tab', 'summary')
    st.session_state.setdefault('fact_index', 0)
    st.session_state.setdefault('question_index', 0)
    st.session_state.setdefault('last_prompt', "")
    st.session_state.setdefault('response_data', None)

def render_card(title, content, bg_color, border_color):
    st.markdown(f"""
        <div style="{SHARED_CARD_STYLE.format(bg_color=bg_color, border_color=border_color)}">
            <h3 style="color: #000000; margin-bottom: 10px;">{title}</h3>
            <p style="font-size: 16px; color: #000000; white-space: pre-wrap;">{content}</p>
            <div style="{STICKER_DECORATION}"></div>
        </div>
    """, unsafe_allow_html=True)

# ---------- UI Renderers ----------

def render_summary_tab(prompt, summary, bg_color, border_color):
    render_card(f"📝 About {prompt}", summary, bg_color, border_color)

def render_list_tab(title, items):
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>", unsafe_allow_html=True) if items else st.info("No items available.")

def render_flashcard_tab(facts, bg_color, border_color):
    if facts:
        index = st.session_state.fact_index
        render_card(f"📘 Fact {index + 1}", facts[index], bg_color, border_color)

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.button("⬅️", on_click=lambda: update_index('fact_index', -1), key="prev_fact_btn")
        with col4: st.button("➡️", on_click=lambda: update_index('fact_index', 1), key="next_fact_btn")
    else:
        st.info("No facts available.")

def render_question_flashcard(questions, bg_color, border_color):
    if not questions:
        st.info("No questions available.")
        return

    index = st.session_state.question_index
    qdata = questions[index]
    question, choices, correct = qdata['question'], qdata['choices'], qdata['correct']
    radio_key, submit_key, feedback_key = f"q_radio_{index}", f"q_submit_{index}", f"q_feedback_{index}"

    render_card(f"❓ Question {index + 1}", question, bg_color, border_color)
    selected = st.radio("Choose your answer:", choices, key=radio_key)

    if st.button("Submit", key=submit_key):
        if selected == correct:
            st.session_state[feedback_key] = ("Correct! 🎉", "success")
        else:
            st.session_state[feedback_key] = (f"Incorrect. The correct answer is: {correct}", "error")

    if feedback_key in st.session_state:
        msg, msg_type = st.session_state[feedback_key]
        (st.success if msg_type == "success" else st.error)(msg)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.button("⬅️", on_click=lambda: update_index('question_index', -1), key="prev_question_btn")
    with col4: st.button("➡️", on_click=lambda: update_index('question_index', 1), key="next_question_btn")

def update_index(index_key, step):
    items = st.session_state.response_data.get(index_key.replace("_index", "s"), [])
    if items:
        st.session_state[index_key] = (st.session_state[index_key] + step) % len(items)

def render_tab_buttons():
    col1, col2, col3 = st.columns(3)
    with col1: st.button("Summary", on_click=lambda: set_tab("summary"), key="tab_summary")
    with col2: st.button("Facts", on_click=lambda: set_tab("facts"), key="tab_facts")
    with col3: st.button("Questions", on_click=lambda: set_tab("questions"), key="tab_questions")

def set_tab(tab_name):
    st.session_state.active_tab = tab_name

def showResponseCard(prompt, response):
    bg_color = random.choice(POST_IT_COLORS)
    border_color = darker_color(bg_color)

    with st.container():
        st.markdown(f"<div class='card'><h3>Generated FlashCard about {prompt}</h3><hr>", unsafe_allow_html=True)
        render_tab_buttons()

        tab = st.session_state.active_tab
        if tab == 'summary':
            render_summary_tab(prompt, response.get('summary', 'No summary available'), bg_color, border_color)
        elif tab == 'facts':
            render_flashcard_tab(response.get('facts', []), bg_color, border_color)
        elif tab == 'questions':
            render_question_flashcard(response.get('questions', []), bg_color, border_color)

# ---------- Main App ----------

def mainUI(debugUI=False):
    setupUI()
    initialize_state()

    engine = KnowledgeEngine() if not debugUI else None

    # Header
    col1, col2 = st.columns([1, 6])
    with col1: st.image("src/images/logo.png", width=60)
    with col2: st.title("AutoFlash")

    st.markdown(
        "<h5 style='font-weight: normal;'>AutoFlash uses AI and Knowledge Graphs to instantly turn complex information into clear, personalized flashcards, helping you study faster and more effectively.</h5>",
        unsafe_allow_html=True
    )

    # Input
    prompt = st.text_input("Enter your theme:")
    if st.button("Generate", type="primary") and prompt:
        with st.spinner("Processing..."):
            if debugUI:
                response = {
                    "facts": ["This a great Fact about the topic", "Wow I didn’t know that", "Now I know more about the topic"],
                    "questions": [
                        {"question": "Is this a question?", "choices": ["1A", "1B", "1C", "1D"], "correct": "1A"},
                        {"question": "Is this question 2?", "choices": ["2A", "2B", "2C", "2D"], "correct": "2B"}
                    ],
                    "summary": "This is a concise summary explaining the topic in a few lines."
                }
            else:
                response = engine.getCombinedResponse(prompt)

            st.session_state.response_data = response
            st.session_state.last_prompt = prompt
            st.session_state.fact_index = 0
            st.session_state.question_index = 0
            st.session_state.active_tab = 'summary'
            
    elif st.session_state.response_data:
        prompt = st.session_state.last_prompt

    if st.session_state.response_data:
        showResponseCard(prompt, st.session_state.response_data)
