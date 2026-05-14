from pathlib import Path
import shutil
import re

from groq import Groq
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import (
    DATA_PATH,
    VECTOR_STORE_PATH,
    GROQ_API_KEY,
    GROQ_MODEL,
    EMBEDDING_MODEL
)


client = Groq(api_key=GROQ_API_KEY)


def load_documents():
    loader = PyPDFDirectoryLoader(DATA_PATH)
    return loader.load()


def clean_documents(documents):
    cleaned_docs = []

    junk_patterns = [
        r"references",
        r"bibliography",
        r"copyright",
        r"all rights reserved",
        r"doi:",
        r"springer",
        r"received:",
        r"accepted:",
        r"published online:",
        r"author contributions",
        r"conflict of interest",
        r"acknowledg",
        r"funding"
    ]

    for doc in documents:
        text = doc.page_content.lower()

        if len(text.strip()) < 200:
            continue

        if any(re.search(pattern, text) for pattern in junk_patterns):
            continue

        cleaned_docs.append(doc)

    return cleaned_docs


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80
    )

    return splitter.split_documents(documents)


embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

def get_embeddings():
    return embeddings


def create_vector_store(chunks):
    embeddings = get_embeddings()

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_STORE_PATH)
    )


def load_vector_store():
    embeddings = get_embeddings()

    return Chroma(
        persist_directory=str(VECTOR_STORE_PATH),
        embedding_function=embeddings
    )


def build_database():
    if VECTOR_STORE_PATH.exists():
        shutil.rmtree(VECTOR_STORE_PATH)

    docs = load_documents()
    cleaned_docs = clean_documents(docs)
    chunks = split_documents(cleaned_docs)

    create_vector_store(chunks)

    return {
        "pages_loaded": len(docs),
        "cleaned_pages": len(cleaned_docs),
        "chunks_created": len(chunks)
    }


def ask_question(question):
    vector_db = load_vector_store()

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 15
        }
    )

    results = retriever.invoke(question)

    sources = set()

    for doc in results:
        source_file = Path(doc.metadata.get("source", "Unknown")).name
        sources.add(source_file)

    context = "\n\n".join(doc.page_content for doc in results)

    prompt = f"""
You are an expert document research assistant.

Answer ONLY from the provided context.

Rules:
- Mention exact methods, models, datasets, or findings if present
- Do not hallucinate
- If evidence is insufficient, say so clearly
- Keep answer concise and factual

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": list(sources)
    }