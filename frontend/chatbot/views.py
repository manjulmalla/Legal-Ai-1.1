from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
import pickle
import numpy as np

# Greeting detection function
def is_greeting(message):
    """Check if the message is a greeting"""
    greetings = [
        'hi', 'hello', 'hey', 'namaste', 'hola', 'yo', 'hii',
        'hello bot', 'hi assistant', 'hi bot', 'hello assistant',
        'good morning', 'good afternoon', 'good evening'
    ]
    message_lower = message.lower().strip()
    # Remove punctuation for comparison
    import re
    message_clean = re.sub(r'[^\w\s]', '', message_lower)
    return message_clean in greetings or message_lower in greetings


# Answer formatter for legal questions
def format_legal_answer(question, context):
    """Format legal answer using context from search results"""
    # Check if it's a greeting
    if is_greeting(question):
        return "Hi, I'm your Legal AI Assistant. How can I help you today?"
    
    # Check if context is empty or has no results
    if not context or 'results' not in context or not context['results']:
        return "No relevant legal information found."
    
    results = context['results']
    
    # Build formatted answer
    answer_parts = []
    
    # Short summary (2-3 lines)
    answer_parts.append(f"Based on your query about '{question}', here is the relevant legal information:")
    answer_parts.append("")
    
    # Bullet points with important details
    for i, result in enumerate(results, 1):
        law = result.get('law', 'Unknown Law')
        section = result.get('section', 'N/A')
        title = result.get('title', 'N/A')
        content = result.get('content', '')
        score = result.get('score', 0)
        
        # Truncate content if too long
        if len(content) > 300:
            content = content[:300] + '...'
        
        answer_parts.append(f"• **{law} - {section}**: {title}")
        answer_parts.append(f"  {content}")
        answer_parts.append(f"  (Relevance: {score:.1%})")
        answer_parts.append("")
    
    # Final note
    answer_parts.append("For complete details, please refer to the full legal document.")
    
    return "\n".join(answer_parts)


# Load preprocessed data from pickle file
def load_preprocessed_data():
    """Load preprocessed data from pickle file"""
    try:
        # Get the directory where the pickle file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pickle_path = os.path.join(current_dir, '..', 'static', 'data', 'preprocessed_laws.pkl')
        pickle_path = os.path.normpath(pickle_path)
        
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        
        return data
    except Exception as e:
        return {'error': str(e)}

# Load preprocessed data at module level (once when Django starts)
preprocessed_data = load_preprocessed_data()

def vectorize_query(query, vocab_index, idf, V):
    """Vectorize query using TF-IDF"""
    # Simple preprocessing (no NLTK dependency)
    import re
    text = query.lower()
    text = re.sub(r'[^\w\s]', '', text)
    tokens = text.split()
    
    # Manual stopwords
    stop_words = {
        "shall", "may", "act", "law", "section", "court", "person",
        "thereof", "therein", "hereby", "upon", "within", "without",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall"
    }
    tokens = [word for word in tokens if word not in stop_words]
    
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

def execute_search(query):
    """Execute search using preprocessed data"""
    try:
        if 'error' in preprocessed_data:
            return {'error': preprocessed_data['error']}
        
        document_matrix = preprocessed_data['document_matrix']
        metadata = preprocessed_data['metadata']
        vocab_index = preprocessed_data['vocab_index']
        idf = preprocessed_data['idf']
        V = preprocessed_data['V']
        
        results, keywords = search(query, document_matrix, metadata, vocab_index, idf, V, top_k=3)
        
        # Format results for response
        formatted_results = []
        for meta, score in results:
            formatted_results.append({
                'law': meta.get('law', ''),
                'section': meta.get('section', ''),
                'title': meta.get('title', ''),
                'content': meta.get('content', ''),
                'score': float(score)
            })
        
        return {'results': formatted_results, 'keywords': keywords}
    except Exception as e:
        return {'error': str(e)}

def chat(request):
    """Handle chat page and chat API requests"""
    # Initialize chat history in session if not exists
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    
    messages = []
    
    if request.method == 'POST':
        # Handle form submission
        user_query = request.POST.get('message', '')
        if user_query:
            # Add user message to chat
            messages.append({'text': user_query, 'sender': 'user'})
            
            # Execute search
            answer = execute_search(user_query)
            
            # Format answer using the new formatter
            formatted_answer = format_legal_answer(user_query, answer)
            messages.append({'text': formatted_answer, 'sender': 'ai'})
            
            # Save conversation to chat history
            conversation = {
                'id': len(request.session['chat_history']) + 1,
                'title': user_query[:50] + '...' if len(user_query) > 50 else user_query,
                'messages': messages.copy(),
                'timestamp': str(request.session.get('_session_id', ''))
            }
            request.session['chat_history'].append(conversation)
            request.session.modified = True
    
    # Get chat history for sidebar
    chat_history = request.session.get('chat_history', [])
    
    # Render template with messages and chat history
    return render(request, 'chatbot/chat.html', {
        'messages': messages,
        'chat_history': chat_history
    })

def chat_view(request):
    """Render chat.html template"""
    return render(request, 'chatbot/chat.html')

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Send a message and get response"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        answer = execute_search(user_message)
        
        # Format answer using the new formatter
        formatted_answer = format_legal_answer(user_message, answer)
        
        return JsonResponse({'answer': formatted_answer})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_conversations(request):
    """Get list of conversations"""
    # Placeholder implementation
    return JsonResponse({'conversations': []})

def get_conversation_history(request, conversation_id):
    """Get conversation history"""
    # Placeholder implementation
    return JsonResponse({'messages': []})
