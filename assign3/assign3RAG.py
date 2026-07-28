"""
Assignment 3 — RAG with a Word Document
Topic: Valorant Beginner Strategy Guide

Install:
    pip install chromadb sentence-transformers python-docx langchain-text-splitters requests

Optional for real LLM answers:
    Install Ollama
    Run:
        ollama pull llama2
        ollama serve
"""

from pathlib import Path
import requests

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOCX_FILE = "valorant_rag_guide.docx"
COLLECTION_NAME = "valorant_rag_collection"


def load_docx_text(file_path):
    """Load text from a Word .docx file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {file_path}. "
            "Make sure the Word document is in the same folder as this Python file."
        )

    document = Document(path)

    paragraphs = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def chunk_text(text):
    """Split the document text into smaller chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120
    )

    chunks = splitter.split_text(text)
    return chunks


def build_vector_db(chunks):
    """Create a ChromaDB collection and store embedded chunks."""
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    client = chromadb.Client()

    # Delete old collection so the script can run many times
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )

    ids = [f"chunk_{i}" for i in range(1, len(chunks) + 1)]

    metadatas = [
        {
            "source": DOCX_FILE,
            "chunk_number": i
        }
        for i in range(1, len(chunks) + 1)
    ]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

    return collection


def retrieve_context(collection, question, n_results=3):
    """Retrieve the most relevant chunks for a question."""
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return documents, metadatas, distances


def generate_answer_with_ollama(question, context_chunks):
    """
    Generate an answer using Ollama if it is running locally.
    If Ollama is not available, return a fallback answer using the retrieved context.
    """
    context_text = "\n\n".join(context_chunks)

    prompt = f"""
You are answering questions using only the provided context from a Word document.

Context:
{context_text}

Question:
{question}

Answer in 3-5 clear sentences.
If the answer is not in the context, say that the document does not provide enough information.
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()["response"].strip()

        return (
            "Ollama returned an error, so here is a fallback answer based on the retrieved context:\n"
            + context_chunks[0]
        )

    except requests.exceptions.RequestException:
        return (
            "Ollama is not running, so here is a fallback answer based on the retrieved context:\n"
            + context_chunks[0]
        )


def main():
    print("Loading Word document...")
    text = load_docx_text(DOCX_FILE)

    print("Splitting document into chunks...")
    chunks = chunk_text(text)
    print(f"Total chunks created: {len(chunks)}")

    print("Creating vector database and storing embeddings...")
    collection = build_vector_db(chunks)
    print(f"Chunks stored in ChromaDB: {collection.count()}")

    questions = [
        "Why is communication important during a match?",
        "How should a team decide what to buy before a round?",
        "How do different character types support the team?",
        "Why is controlling space on the map useful?",
        "What mistakes should new players avoid?"
    ]

    print("\nRAG RESULTS")
    print("=" * 80)

    for question_number, question in enumerate(questions, start=1):
        context_chunks, metadatas, distances = retrieve_context(
            collection=collection,
            question=question,
            n_results=3
        )

        answer = generate_answer_with_ollama(question, context_chunks)

        print(f"\nQuestion {question_number}: {question}")
        print("-" * 80)

        print("\nLLM Answer:")
        print(answer)

        print("\nRetrieved Context Chunks:")
        for i, (chunk, metadata, distance) in enumerate(
            zip(context_chunks, metadatas, distances),
            start=1
        ):
            print(f"\nContext Chunk {i}")
            print(f"Distance: {distance:.4f}")
            print(f"Metadata: {metadata}")
            print(chunk)

        print("\n" + "=" * 80)

    print(
        "\nShort Analysis:\n"
        "This RAG system loads a Word document about Valorant, splits it into chunks, "
        "and stores the chunks as embeddings in ChromaDB.\n"
        "When the user asks a question, the question is also embedded and compared "
        "against the stored document chunks.\n"
        "The retrieved chunks are then used as context for generating the answer, "
        "so the answer is based on the Word document rather than only general model knowledge.\n"
        "Printing the retrieved context chunks makes the result easier to check, because it shows "
        "which parts of the document were used.\n"
        "Smaller distance values usually mean the retrieved chunk is more semantically similar "
        "to the question.\n"
    )


if __name__ == "__main__":
    main()