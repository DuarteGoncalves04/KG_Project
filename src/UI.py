from KnowledgeEngine import KnowledgeEngine
import streamlit as st
import random

# ---------- Constants ----------

POST_IT_COLORS = ["#cdfc93", "#ff7ecd", "#71d7ff", "#ce81ff", "#fff68b"]
SHARED_CARD_STYLE = (
    "background: {bg_color}; "
    "padding: 25px 20px; "
    "border-radius: 12px; "
    "max-width: 600px; "
    "box-shadow: 5px 7px 15px rgba(0,0,0,0.3); "
    "font-family: 'Comic Sans MS', cursive, sans-serif; "
    "border: 2px solid {border_color}; "
    "margin-top: 20px; "
    "position: relative;"
)

STICKER_DECORATION = (
    "position: absolute; "
    "top: 0px; "
    "left: -15px; "
    "width: 60px; "
    "height: 15px; "
    "background: repeating-linear-gradient(45deg, #FFD580, #FFD580 5px, #FFA500 5px, #FFA500 10px); "
    "border-radius: 3px; "
    "box-shadow: 0 1px 3px rgba(0,0,0,0.15); "
    "transform: rotate(-40deg);"
)



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

def render_card(title, content, bg_color, border_color, question_mode=False, correct=0, total=0):
    base_style = SHARED_CARD_STYLE.format(bg_color=bg_color, border_color=border_color)

    score_html = ""
    if question_mode:
        score_html = (
            f"<div style='position: absolute; top: 10px; right: 15px; "
            f"font-size: 14px; font-weight: bold; color: #333;'>✅ {correct}/{total}</div>"
        )

    html_parts = [
        f"<div style='position: relative; margin-top: 15px; margin-bottom: 15px; {base_style}'>",
        f"<div style='{STICKER_DECORATION}'></div>",
        f"<h3 style='color: #000000; margin-bottom: 10px;'>{title}</h3>",
        f"<p style='font-size: 16px; color: #000000; white-space: pre-wrap; margin: 0;'>{content}</p>",
        score_html,
        "</div>"
    ]

    html_str = "".join(html_parts)
    st.markdown(html_str, unsafe_allow_html=True)
    return html_str



# ---------- UI Renderers ----------

def render_summary_tab(prompt, summary, bg_color, border_color):
    card_sum_html = render_card(f"📝 About {prompt}", summary, bg_color, border_color)
    
    if st.button("Export as PNG"):
        export_html_as_png(card_sum_html)

def render_list_tab(title, items):
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>", unsafe_allow_html=True) if items else st.info("No items available.")


def render_flashcard_tab(facts, bg_color, border_color):
    if facts:
        index = st.session_state.fact_index
        card_tab_html = render_card(f"📘 Fact {index + 1}", facts[index], bg_color, border_color)

        # Custom column widths to control button placement
        col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.05])

        with col1:
            st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
            st.button("⬅️", on_click=lambda: update_index('fact_index', -1), key="prev_fact_btn")

        with col4:
            st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
            st.button("➡️", on_click=lambda: update_index('fact_index', 1), key="next_fact_btn")
            
            
        if st.button("Export as PNG"):
            export_html_as_png(card_tab_html)
        
    else:
        st.info("No facts available.")


def render_question_flashcard(questions, bg_color, border_color):
    if not questions:
        st.info("No questions available.")
        return

    index = st.session_state.question_index
    qdata = questions[index]
    question, choices, correct = qdata['question'], qdata['options'], qdata['correct_answer']
    radio_key = f"q_radio_{index}"
    feedback_key = f"q_feedback_{index}"
    submitted_key = f"submitted_{index}"

    # Compute score once (before rendering card) based on current session_state
    correct_count, answered_count = get_question_score(questions)

    # Render the question card first (with score)
    render_card(
        f"❓ Question {index + 1}",
        question,
        bg_color,
        border_color,
        question_mode=True,
        correct=correct_count,
        total=answered_count
    )

    # Get previously selected answer if available
    saved_answer = st.session_state.get(radio_key)

    # Show radio options after the card
    if saved_answer is None and not st.session_state.get(submitted_key, False):
        selected = st.radio(
            "Choose your answer:",
            choices,
            index=None,
            key=f"{radio_key}_tmp"
        )
        if selected is not None:
            st.session_state[radio_key] = selected
    else:
        selected = st.radio(
            "Choose your answer:",
            choices,
            index=choices.index(saved_answer) if saved_answer in choices else 0,
            key=radio_key
        )

    # Handle submit button
    if st.button("Submit", key=f"q_submit_{index}"):
        selected = st.session_state.get(radio_key)
        if selected is None:
            st.warning("Please select an answer before submitting.")
        else:
            st.session_state[submitted_key] = True
            if selected == correct:
                st.session_state[feedback_key] = ("Correct! 🎉", "success")
            else:
                st.session_state[feedback_key] = (f"Incorrect. The correct answer is: {correct}", "error")

    # Show feedback only if submitted
    if st.session_state.get(submitted_key):
        selected = st.session_state.get(radio_key)
        if selected is not None:
            is_correct = (selected == correct)
            render_feedback(is_correct, correct)

    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.05])
    with col1:
        st.button("⬅️", on_click=lambda: update_index('question_index', -1), key=f"prev_question_{index}")
    with col4:
        st.button("➡️", on_click=lambda: update_index('question_index', 1), key=f"next_question_{index}")


def update_index(index_key, step):
    items = st.session_state.response_data.get(index_key.replace("_index", "s"), [])
    if not items:
        return

    current_index = st.session_state[index_key]
    new_index = (current_index + step) % len(items)

    # Only clear feedback view, not saved selections
    st.session_state.pop(f"q_feedback_{current_index}", None)
    st.session_state[index_key] = new_index

def get_question_score(questions):
    correct_count = 0
    answered_count = 0
    for i, q in enumerate(questions):
        if st.session_state.get(f"submitted_{i}", False):
            answered_count += 1
            selected = st.session_state.get(f"q_radio_{i}")
            if selected == q['correct_answer']:
                correct_count += 1
    return correct_count, answered_count


def render_feedback(is_correct, correct_answer, max_width="600px", margin="margin-bottom: 15px;"):
    if is_correct:
        color_style = "background-color: #65db6d; color: #155724; padding: 10px; border-radius: 5px; font-weight: bold;"
        message = "Correct! 🎉"
    else:
        color_style = "background-color: #d65e62; color: #721c24; padding: 10px; border-radius: 5px; font-weight: bold;"
        message = f"Incorrect. The correct answer is: {correct_answer}"

    st.markdown(
        f"""
        <div style="max-width: {max_width}; {margin} {color_style}">
            {message}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_tab_buttons():
    col1, col2, col3 = st.columns([1, 0.9, 0.79])
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
            
            
# Export Flashcard 
def export_html_as_png(html_str, filename="card.png"):
    export_script = f"""
    <div id="hidden-card" style="
      position: absolute;
      left: 0;
      top: 0;
      opacity: 0;
      pointer-events: none;
      z-index: -1;
    ">
      <div id="capture" style="display: inline-block;">
        {html_str}
      </div>
    </div>

    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
      window.setTimeout(() => {{
        html2canvas(document.getElementById('capture'), {{
          backgroundColor: null,
          scale: window.devicePixelRatio
        }}).then(canvas => {{
          canvas.toBlob(blob => {{
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{filename}';
            a.click();
            URL.revokeObjectURL(url);
          }});
        }});
      }}, 500);
    </script>
    """
    st.components.v1.html(export_script, height=0, width=0, scrolling=False)


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
        # --- Full session cleanup (except prompt) ---
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Optionally re-set prompt (if needed after clearing)
        st.session_state["last_prompt"] = prompt
        
        with st.spinner("Processing..."):
            if debugUI:
                response = {
                    "facts": ["This a great Fact about the topic", "Wow I didn’t know that", "Now I know more about the topic"],
                    "questions": [
                        {"question": "Is this a question?", "options": ["1A", "1B", "1C", "1D"], "correct_answer": "1A"},
                        {"question": "Is this question 2?", "options": ["2A", "2B", "2C", "2D"], "correct_answer": "2B"}
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
