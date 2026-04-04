"""
Preprocessing script for legal documents.
This script loads JSON law files, preprocesses them, builds TF-IDF matrix,
and saves the results to a pickle file for fast loading in Django.
"""

import json
import os
import re
import numpy as np
import pickle
from nltk.corpus import stopwords
import nltk

# Download stopwords if not already downloaded
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

# Manual stopword definition for legal terms
legal_stopwords = {
    "shall", "may", "act", "law", "section", "court", "person",
    "thereof", "therein", "hereby", "upon", "within", "without"
}

stop_words.update(legal_stopwords)

def clean_text(text):
    """Lowercase and remove punctuation"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def tokenize(text):
    """Tokenize text by splitting on whitespace"""
    return text.split()

def remove_stopwords(tokens):
    """Remove stopwords from tokens"""
    return [word for word in tokens if word not in stop_words]

def preprocess(text):
    """Full preprocessing pipeline"""
    text = clean_text(text)
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    return tokens

def load_all_laws(folder_path):
    """Load all JSON law files from folder"""
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
    """Build TF-IDF matrix from documents"""
    # Preprocess Documents
    tokenized_docs = [preprocess(doc) for doc in documents]

    # Build vocabulary
    vocab = set()
    for doc in tokenized_docs:
        vocab.update(doc)

    vocab = list(vocab)
    vocab_index = {word: i for i, word in enumerate(vocab)}

    N = len(tokenized_docs)  # Docs no.
    V = len(vocab)  # Unique tokens no.
    tf_matrix = np.zeros((N, V))

    for doc_idx, meta in enumerate(metadata):
        title = meta["title"]
        content = meta["content"]

        title_tokens = preprocess(title)
        content_tokens = preprocess(content)

        tokens = []

        # Title words weighted higher
        for word in title_tokens:
            tokens.extend([word] * 3)

        # Content words normal
        tokens.extend(content_tokens)

        for word in tokens:
            if word in vocab_index:
                tf_matrix[doc_idx][vocab_index[word]] += 1

        if len(tokens) > 0:
            tf_matrix[doc_idx] = tf_matrix[doc_idx] / len(tokens)

    # Document Frequency
    df = np.zeros(V)

    for word, idx in vocab_index.items():
        count = 0
        for doc in tokenized_docs:
            if word in doc:
                count += 1
        df[idx] = count

    # IDF
    idf = np.log(N / (df + 1))

    # TF-IDF Matrix
    document_matrix = tf_matrix * idf

    return document_matrix, vocab_index, idf

def vectorize_query(query, vocab_index, idf, V):
    """Vectorize query using TF-IDF"""
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
    """Calculate cosine similarity between two vectors"""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot / (norm1 * norm2)

def search(query, document_matrix, metadata, vocab_index, idf, V, top_k=3):
    """Search for relevant documents"""
    query_vec, keywords = vectorize_query(query, vocab_index, idf, V)

    scores = []

    for i, doc_vec in enumerate(document_matrix):
        sim = cosine_similarity(query_vec, doc_vec)
        scores.append((i, sim))

    scores.sort(key=lambda x: x[1], reverse=True)

    top_results = scores[:top_k]

    results = []

    for idx, score in top_results:
        results.append((metadata[idx], score))

    return results, keywords

def main():
    """Main preprocessing function"""
    print("Loading legal documents...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load all laws from current directory
    documents, metadata = load_all_laws(script_dir)
    
    print(f"Total Documents: {len(documents)}")
    
    print("Building TF-IDF matrix...")
    document_matrix, vocab_index, idf = build_tfidf_matrix(documents, metadata)
    
    V = len(vocab_index)
    print(f"TF-IDF Matrix Shape: {document_matrix.shape}")
    
    # Save preprocessed data to pickle file
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
    
    print(f"Preprocessed data saved to: {output_file}")
    print("Preprocessing complete!")

if __name__ == "__main__":
    main()
