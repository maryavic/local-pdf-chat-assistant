import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


def process_pdf(file, model_name):
    """Optimized PDF processing"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_file_path = tmp_file.name

        loader = PyPDFLoader(tmp_file_path)
        documents = loader.load()

        # Optimized text splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "!", "?", ",", " "],
            length_function=len
        )
        splits = text_splitter.split_documents(documents)

        embeddings = OllamaEmbeddings(
            model=model_name,
            base_url="http://localhost:11434"
        )

        # Correct FAISS usage
        vector_store = FAISS.from_documents(splits, embeddings)
        return vector_store
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")
    finally:
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)


def create_chain(vector_store, model_name):
    """Create optimized conversation chain"""
    llm = OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434",
        temperature=0.7,
        num_ctx=2048
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 2}
        ),
        memory=memory,
        return_source_documents=True,
        verbose=False
    )

    return chain
