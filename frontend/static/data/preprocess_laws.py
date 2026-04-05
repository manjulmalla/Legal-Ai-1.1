"""
[V1.1] Preprocessing script for legal documents.
Change log:
- Better text cleaning (preserves structure)
- Safer stopword handling (keeps legal meaning words)
- Improved IDF formula (smoothed)
- Minor fixes
"""

import json
import os
import re
import numpy as np
import pickle
from nltk.corpus import stopwords
import nltk
import unicodedata

# Download stopwords *if not already downloaded
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

# Reduced legal stopwords (keep important legal words like "shall", "may")
legal_stopwords = {
    "act", "law", "section", "court", "person",
    "thereof", "therein", "hereby", "upon", "within", "without"
}

stop_words.update(legal_stopwords)

def clean_text(text):
    """Improved cleaning while preserving legal structure"""
    
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)

    # Lowercase
    text = text.lower()

    # Remove website references
    text = re.sub(r"www\.\S+", "", text)

    # Fix hyphenated line breaks (PDF issue)
    text = re.sub(r'\s*-\s*\n\s*', '', text)

    # Remove stray hyphens
    text = re.sub(r'\s-\s', ' ', text)

    # Keep alphanumeric + parentheses (important for (a), (1))
    text = re.sub(r'[^\w\s\(\)]', '', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def tokenize(text):
    return text.split()


def remove_stopwords(tokens):
    return [word for word in tokens if word not in stop_words]


def preprocess(text):
    text = clean_text(text)
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    return tokens


def load_all_laws(folder_path):
    documents = []
    metadata = []

    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            law_name = file.replace(".json", "")

            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                data = json.load(f)

                for sec_no, section in data.items():
                    title = section.get("title", "")
                    content = section.get("content", "")

                    doc_text = f"{sec_no} : {title} {content}"

                    documents.append(doc_text)

                    metadata.append({
                        "law": law_name,
                        "section": sec_no,
                        "title": title,
                        "content": content
                    })

    return documents, metadata


def build_tfidf_matrix(documents, metadata):
    tokenized_docs = [preprocess(doc) for doc in documents]

    # Build vocabulary
    vocab = set()
    for doc in tokenized_docs:
        vocab.update(doc)

    vocab = list(vocab)
    vocab_index = {word: i for i, word in enumerate(vocab)}

    N = len(tokenized_docs)
    V = len(vocab)
    tf_matrix = np.zeros((N, V))

    for doc_idx, meta in enumerate(metadata):
        title_tokens = preprocess(meta["title"])
        content_tokens = preprocess(meta["content"])

        tokens = []

        # Title weighting
        for word in title_tokens:
            tokens.extend([word] * 3)

        tokens.extend(content_tokens)

        for word in tokens:
            if word in vocab_index:
                tf_matrix[doc_idx][vocab_index[word]] += 1

        if len(tokens) > 0:
            tf_matrix[doc_idx] = tf_matrix[doc_idx] / len(tokens)

    # Document Frequency
    df = np.zeros(V)

    for word, idx in vocab_index.items():
        df[idx] = sum(1 for doc in tokenized_docs if word in doc)

    # Improved IDF (smoothed)
    idf = np.log((N + 1) / (df + 1)) + 1

    document_matrix = tf_matrix * idf

    return document_matrix, vocab_index, idf


def vectorize_query(query, vocab_index, idf, V):
    tokens = preprocess(query)
    vec = np.zeros(V)

    for word in tokens:
        if word in vocab_index:
            idx = vocab_index[word]
            vec[idx] += 1

    if len(tokens) > 0:
        vec = vec / len(tokens)

    vec = vec * idf

    return vec, tokens


def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot / (norm1 * norm2)


def search(query, document_matrix, metadata, vocab_index, idf, V, top_k=3):
    query_vec, keywords = vectorize_query(query, vocab_index, idf, V)

    scores = []

    for i, doc_vec in enumerate(document_matrix):
        sim = cosine_similarity(query_vec, doc_vec)
        scores.append((i, sim))

    scores.sort(key=lambda x: x[1], reverse=True)

    top_results = scores[:top_k]

    results = [(metadata[idx], score) for idx, score in top_results]

    return results, keywords


def main():
    print("Loading legal documents...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    documents, metadata = load_all_laws(script_dir)

    print(f"Total Documents: {len(documents)}")

    print("Building TF-IDF matrix...")
    document_matrix, vocab_index, idf = build_tfidf_matrix(documents, metadata)

    V = len(vocab_index)
    print(f"TF-IDF Matrix Shape: {document_matrix.shape}")

    output_file = os.path.join(script_dir, 'preprocessed_laws.pkl')

    with open(output_file, 'wb') as f:
        pickle.dump({
            'documents': documents,
            'metadata': metadata,
            'document_matrix': document_matrix,
            'vocab_index': vocab_index,
            'idf': idf,
            'V': V
        }, f)

    print(f"Saved to: {output_file}")
    print("Done!")


if __name__ == "__main__":
    main()