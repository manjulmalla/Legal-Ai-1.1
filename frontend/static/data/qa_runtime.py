import pickle
import time
from preprocess_laws import search  # import search function

# Load preprocessed data
def load_data(pkl_path):
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    return data


def format_output(query, results, keywords, response_time):
    print("\n" + "="*60)
    print("🔍 LEGAL QUERY RESULT")
    print("="*60)

    print(f"\n📝 Query: {query}")
    print(f"⏱ Response Time: {round(response_time, 3)} sec")

    print(f"\n🔑 Keywords extracted: {', '.join(keywords)}")

    print("\n📚 Top Relevant Sections:\n")

    for i, (meta, score) in enumerate(results, 1):
        print(f"{i}. {meta['law'].upper()} - Section {meta['section']}")
        print(f"   Title: {meta['title']}")
        print(f"   Relevance Score: {round(score, 3)}")

        # Show shortened preview (clean output)
        content_preview = meta['content'][:300] + "..." if len(meta['content']) > 300 else meta['content']
        print(f"   Content: {content_preview}")
        print("-"*60)


def run_query(query, data):
    start_time = time.time()

    results, keywords = search(
        query,
        data['document_matrix'],
        data['metadata'],
        data['vocab_index'],
        data['idf'],
        data['V'],
        top_k=3
    )

    end_time = time.time()

    format_output(query, results, keywords, end_time - start_time)


def main():
    print("📂 Loading preprocessed data...")

    data = load_data("preprocessed_laws.pkl")

    print("Ready! Ask your legal questions.\n")

    while True:
        query = input("💬 Enter your query (or type 'exit'): ")

        if query.lower() == "exit":
            print("👋 Exiting...")
            break

        run_query(query, data)


if __name__ == "__main__":
    main()