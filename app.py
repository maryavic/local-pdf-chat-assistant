import streamlit as st
from pdf_processor import process_pdf, create_chain
import logging
import warnings

# Configure logging and warnings
logging.basicConfig(level=logging.WARNING)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Page configuration
st.set_page_config(
    page_title="Local PDF Chat Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        :root {
            --primary-color: #2196F3;
        }
        .stButton>button {
            background-color: #2196F3;
            color: white;
        }
        .stButton>button:hover {
            background-color: #1976D2;
            color: white;
        }
        .stRadio>label {
            color: #2196F3;
        }
        .sidebar .sidebar-content {
            background-color: #E3F2FD;
        }
        .st-bb {
            border-bottom-color: #2196F3;
        }
        .st-at {
            background-color: #E3F2FD;
        }
        .st-emotion-cache-16txtl3 {
            background: #E3F2FD;
        }
        .st-emotion-cache-6qob1r {
            background: #E3F2FD;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chain" not in st.session_state:
    st.session_state.chain = None


# Sidebar with original blue theme colors
with st.sidebar:
    st.markdown(
        """
        <div style="
            background-color: #E3F2FD; 
            padding: 20px; 
            border-radius: 10px; 
            color: #1976D2; 
            text-align: center;">
            <h2>Welcome!</h2>
            <p style="font-size: 14px;">
                Upload your PDF and select a model to interact with its content.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<p style='color: #1976D2; font-weight: bold; margin-top: 20px;'>Choose a Model</p>", unsafe_allow_html=True)
    model_name = st.radio(
        "",
        ["llama2", "mistral", "gemma"],
        help="Select the Ollama model to use",
        horizontal=True,
        key="model_selection",
        label_visibility="collapsed"
    )
    
    st.markdown("<p style='color: #1976D2; font-weight: bold; margin-top: 20px;'>Upload Your PDF</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'], help="Upload a PDF file to chat with")

    if uploaded_file:
        if st.button("🔄 Process PDF", type="primary", use_container_width=True):
            with st.spinner("Processing PDF..."):
                try:
                    st.session_state.vector_store = process_pdf(uploaded_file, model_name)
                    st.session_state.chain = create_chain(st.session_state.vector_store, model_name)
                    st.success("✅ PDF processed successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# Main chat interface
st.markdown("<h1 style='text-align: center;'>💬 Local PDF Chat Assistant</h1>", unsafe_allow_html=True)
if st.session_state.vector_store is None:
    st.info("👆 Please upload and process a PDF file to start chatting")

# Display chat messages
for message in st.session_state.messages:
    bubble_class = "user" if message["role"] == "user" else "assistant"
    st.markdown(
        f"<div class='chat-bubble {bubble_class}'>{message['content']}</div>",
        unsafe_allow_html=True
    )
    if "sources" in message:
        with st.expander("📚 View Sources"):
            st.write(message["sources"])

# Chat input and processing
if prompt := st.chat_input("Ask your question about the PDF..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-bubble user'>{prompt}</div>", unsafe_allow_html=True)
    with st.chat_message("assistant"):
        if st.session_state.chain is not None:
            try:
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.chain.invoke({"question": prompt})
                    has_sources = any(doc.page_content.strip() != "" for doc in response["source_documents"])
                    if has_sources:
                        answer = response["answer"]
                        st.markdown(f"<div class='chat-bubble assistant'>{answer}</div>", unsafe_allow_html=True)
                        sources = "\n\n".join(
                            [f"Source {i+1}:\n{doc.page_content}" for i, doc in enumerate(response["source_documents"])]
                        )
                        with st.expander("📚 View Sources"):
                            st.write(sources)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                    else:
                        no_info_msg = "No relevant information found in the PDF."
                        st.markdown(f"<div class='chat-bubble assistant'>{no_info_msg}</div>", unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": no_info_msg})
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please upload and process a PDF first.")
