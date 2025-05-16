from KnowledgeEngine import KnowledgeEngine
import streamlit as st

def setupUI():
    st.set_page_config(
        page_title="KG Project",
        page_icon=":guardsman:",
        layout="centered",
    )

    st.markdown("""
    <style>
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin: 20px 0;
        }
        .kg-result {
            color: #6a11cb;
            font-weight: bold;
        }
        .tab-button {
            margin: 5px;
        }
        .button-container {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

def showResponseCard(prompt, response):
    if isinstance(response, dict):
        # Initialize session state for tab control
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 'answer'
        
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h3>{prompt}</h3>
                <hr>
                <div class="button-container">
            """, unsafe_allow_html=True)
            
            # Create buttons for each tab
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Answer", key="answer_btn", type="primary" if st.session_state.active_tab == 'answer' else 'secondary'):
                    st.session_state.active_tab = 'answer'
            with col2:
                if st.button("Facts", key="facts_btn", type="primary" if st.session_state.active_tab == 'facts' else 'secondary'):
                    st.session_state.active_tab = 'facts'
            with col3:
                if st.button("Questions", key="questions_btn", type="primary" if st.session_state.active_tab == 'questions' else 'secondary'):
                    st.session_state.active_tab = 'questions'
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display content based on active tab
            if st.session_state.active_tab == 'answer':
                st.markdown(f"""
                <h4>Summary Answer</h4>
                <p>{response.get('answer', 'No summary available')}</p>
                """, unsafe_allow_html=True)
            elif st.session_state.active_tab == 'facts':
                st.markdown("""
                <h4>Key Facts</h4>
                <ul>
                    """ + "".join(f"<li>{fact}</li>" for fact in response.get('facts', [])) + """
                </ul>
                """, unsafe_allow_html=True)
            elif st.session_state.active_tab == 'questions':
                st.markdown("""
                <h4>Thought-Provoking Questions</h4>
                <ul>
                    """ + "".join(f"<li>{q}</li>" for q in response.get('questions', [])) + """
                </ul>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Fallback for non-structured responses
        st.markdown(f"""
        <div class="card">
            <h3>{prompt}</h3>
            <hr>
            <p>{response}</p>
        </div>
        """, unsafe_allow_html=True)

def mainUI():
    setupUI()
    engine = KnowledgeEngine()
    st.title("Knowledge Graph Project")
    prompt = st.text_input("Enter your query:")
    if st.button("Search", type="primary"):
        if prompt:
            with st.spinner("Processing..."):
                response = engine.getCombinedResponse(prompt)
            showResponseCard(prompt, response)
        else:
            st.error("Please enter a query.")
