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
        .card{
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
    </style>
    """, unsafe_allow_html=True)

def showResponseCard(prompt, response):
    with st.container():
        st.markdown(f"""
        <div class="card">
            <h3>{prompt}</h3>
            <hr>
            {response.get("llm_response", "")}
            {f'<div class="kg-result">KG Facts: {response.get("kg_results", [])}</div>' if response.get("kg_results") else ""}
        </div>
        """,unsafe_allow_html=True)

def mainUI():
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
