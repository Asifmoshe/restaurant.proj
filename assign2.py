# pip install chromadb sentence-transformers

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Free local embedding model — no API key needed
ef = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.Client()
collection = client.create_collection(
    name="my_collection",
    embedding_function=ef
)

# --- Add your documents here ---
collection.add(
    documents=[
        "The Shawshank Redemption — a story of hope and friendship in prison",
        "Inception — a heist thriller set inside layers of dreams",
        "The Lion King — an animated film about a young lion reclaiming his kingdom",
        "The Godfather — a crime drama about family, power, and loyalty",
        "The Dark Knight — a superhero thriller about chaos and justice",
        "Forrest Gump — a drama about a kind man witnessing historic events",
        "The Matrix — a sci-fi action film about reality and control",
        "Titanic — a romantic disaster film set aboard the famous ship",
        "Jurassic Park — a sci-fi adventure about dinosaurs brought back to life",
        "Gladiator — a historical action drama about revenge in ancient Rome",
        "Finding Nemo — an animated adventure about a father searching for his son",
        "Interstellar — a sci-fi drama about space travel and saving humanity",
        "The Silence of the Lambs — a psychological thriller about catching a serial killer",
        "Toy Story — an animated film about toys that come to life",
        "Avatar — a sci-fi adventure about humans exploring the alien world of Pandora"
    ],
    metadatas=[
        {"genre": "drama",  "year": 1994},
        {"genre": "sci-fi", "year": 2010},
        {"genre": "animation", "year": 1994},
        {"genre": "crime", "year": 1972},
        {"genre": "action", "year": 2008},
        {"genre": "drama", "year": 1994},
        {"genre": "sci-fi", "year": 1999},
        {"genre": "romance", "year": 1997},
        {"genre": "adventure", "year": 1993},
        {"genre": "action", "year": 2000},
        {"genre": "animation", "year": 2003},
        {"genre": "sci-fi", "year": 2014},
        {"genre": "thriller", "year": 1991},
        {"genre": "animation", "year": 1995},
        {"genre": "sci-fi", "year": 2009}
    ],
    ids=["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8", "doc9", "doc10", "doc11", "doc12", "doc13", "doc14", "doc15"]
)

print(f"Collection created with {collection.count()} documents")

# Example: query uses different words than the stored documents
queries = [
    "a movie about escaping a difficult situation",
    "film involving the subconscious mind",
    "story about growing up and taking responsibility",
    "a story about trust, hierarchy, and influence inside a close group",
    "a journey to reunite with someone who was lost"
]

for query in queries:
    results = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    print(f"\n🔍 Query: '{query}'")
    print("-" * 60)
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        print(f"  Distance: {dist:.4f}  |  {doc[:80]}...")
        print(f"  Metadata: {meta}")

print("\nA short analysis:\n")
print("The vector database was able to return semantically related results for each query, even when the exact words from the query did not appear in the documents.\n"
      "The best result was the query 'film involving the subconscious mind', which returned Inception with a low distance of 0.4526.\n"
      "This is a strong semantic match because Inception is about dreams and hidden layers of the mind, even though the query does not use the word dreams.\n"
      "A surprisingly good match was the query 'a story about trust, hierarchy, and influence inside a close group', which returned The Godfather as the top result.\n"
      "This result is interesting because the query did not directly use the words family, power, or loyalty, but the meaning was still close.\n"
      "Some results were less accurate, such as the query about growing up and responsibility not returning The Lion King in the top three.\n"
      "This shows that vector search is powerful, but the quality depends on how detailed the documents are and how the query is written.\n"
      "In general, smaller distances mean the document is more similar to the query.\n"
      "I would use a distance threshold of about 0.65 to decide if a result is relevant, because the stronger matches were usually below this value."
      )
