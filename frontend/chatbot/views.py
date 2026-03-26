from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import json
import os
import re

NODE_API = "http://localhost:7001/api"

# Base directory for the chatbot app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data files are in static/data folder
STATIC_DATA_DIR = os.path.join(settings.BASE_DIR, 'static', 'data')

# Also check the old location for backward compatibility
OLD_DATA_DIR = os.path.join(BASE_DIR, 'data')

# Cache for loaded legal data
legal_data_cache = None


def load_legal_data():
    """
    Load all JSON legal data files from the static/data folder
    """
    global legal_data_cache
    
    if legal_data_cache is not None:
        return legal_data_cache
    
    legal_data_cache = []
    
    # Load from static/data folder
    json_files = [
        'Civil.json',
        'Constitution.json',
        'Criminal1.json',
        'Criminal2.json',
        'Criminal3.json',
        'Evidence_Act.json'
    ]
    
    for filename in json_files:
        # First try static/data folder
        filepath = os.path.join(STATIC_DATA_DIR, filename)
        if not os.path.exists(filepath):
            # Fall back to old location
            filepath = os.path.join(OLD_DATA_DIR, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    legal_data_cache.append({
                        'source': filename.replace('.json', ''),
                        'data': data
                    })
                    print(f"Loaded {filename} successfully")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        else:
            print(f"File not found: {filepath}")
    
    return legal_data_cache


def search_legal_data(query):
    """
    Search through the legal data for relevant information
    Handles both flat structure (Civil.json, Constitution.json, Criminal*.json)
    and nested structure (Evidence_Act.json with chapters -> sections)
    """
    data = load_legal_data()
    query_lower = query.lower()
    results = []
    
    # Keywords to search for
    keywords = query_lower.split()
    
    for source in data:
        source_name = source['source']
        source_data = source['data']
        
        # Check if it's nested structure (chapters -> sections) or flat (sections directly)
        # Evidence_Act.json has: CHAPTER-1 -> Section 1 -> {title, content}
        # Civil.json has: Section 1 -> {title, content}
        first_key = next(iter(source_data.keys()), None)
        is_nested = False
        
        if first_key:
            first_value = source_data[first_key]
            if isinstance(first_value, dict):
                # Check if keys look like chapters (contain 'CHAPTER') or sections
                # If first key contains 'CHAPTER', it's nested
                if 'CHAPTER' in str(first_key).upper():
                    is_nested = True
                else:
                    # Check if this looks like a section directly with title/content
                    if 'title' in first_value and 'content' in first_value:
                        is_nested = False  # Flat structure: Section -> {title, content}
                    else:
                        # Could be nested, check the nested values
                        first_nested_key = next(iter(first_value.keys()), None)
                        if first_nested_key and isinstance(first_value[first_nested_key], dict):
                            nested_item = first_value[first_nested_key]
                            if 'title' in nested_item and 'content' in nested_item:
                                # This is nested: Chapter -> Section -> {title, content}
                                is_nested = True
        
        if is_nested:
            # Nested structure: iterate through chapters, then sections
            for chapter_key, chapter_content in source_data.items():
                for section_key, section_data in chapter_content.items():
                    if not isinstance(section_data, dict):
                        continue
                    
                    title = section_data.get('title', '').lower()
                    content = section_data.get('content', '').lower()
                    
                    # Check if any keyword matches
                    matches = any(keyword in title or keyword in content for keyword in keywords)
                    
                    if matches:
                        results.append({
                            'source': source_name,
                            'section': f"{chapter_key} - {section_key}",
                            'title': section_data.get('title', ''),
                            'content': section_data.get('content', '')[:500],  # Limit content length
                            'relevance': sum(1 for kw in keywords if kw in title or kw in content)
                        })
        else:
            # Flat structure: iterate directly through sections
            for section_key, section_content in source_data.items():
                if not isinstance(section_content, dict):
                    continue
                    
                title = section_content.get('title', '').lower()
                content = section_content.get('content', '').lower()
                
                # Check if any keyword matches
                matches = any(keyword in title or keyword in content for keyword in keywords)
                
                if matches:
                    results.append({
                        'source': source_name,
                        'section': section_key,
                        'title': section_content.get('title', ''),
                        'content': section_content.get('content', '')[:500],  # Limit content length
                        'relevance': sum(1 for kw in keywords if kw in title or kw in content)
                    })
    
    # Sort by relevance (most matches first)
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return results[:5]  # Return top 5 results


def generate_answer(query, search_results):
    """
    Generate a human-readable answer based on search results
    """
    if not search_results:
        return "I couldn't find specific information related to your query in the legal database. Please try a different question or be more specific about the legal topic you're asking about."
    
    answer = "Based on the legal documents, here's what I found:\n\n"
    
    for i, result in enumerate(search_results, 1):
        answer += f"**{result['title']}**\n"
        answer += f"(Source: {result['source']}, Section: {result['section']})\n\n"
        
        content = result['content'].strip()
        if content:
            answer += f"{content}\n\n"
        answer += "---\n\n"
    
    return answer


def chat(request):
    """
    Render chat page - requires authentication
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        return redirect('login')
    
    context = {
        'user': user,
        'token': token,
    }
    return render(request, 'chatbot/chat.html', context)


@csrf_exempt
def send_message(request):
    """
    Handle incoming chat messages and return AI-generated responses
    """
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # Debug: print request info
        print(f"Request method: {request.method}")
        print(f"Request body: {request.body}")
        
        # Parse the request body - support both 'message' and 'question' fields
        if not request.body:
            return JsonResponse({'error': 'Empty request body'}, status=400)
            
        body = json.loads(request.body)
        # Accept either 'message' or 'question' field
        message = body.get('message', '').strip() or body.get('question', '').strip()
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # First, try to search local legal data
        search_results = search_legal_data(message)
        
        # Generate answer from search results
        answer = generate_answer(message, search_results)
        
        # Try to also save conversation to backend (MongoDB)
        token = request.session.get('token')
        if token:
            try:
                # First create/save the user's message
                save_resp = requests.post(
                    f"{NODE_API}/chat/save",
                    json={
                        'message': message,
                        'type': 'user'
                    },
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=5
                )
                print(f"Save user message response: {save_resp.status_code}")
                
                # Then save the bot response
                if save_resp.status_code == 200:
                    save_resp2 = requests.post(
                        f"{NODE_API}/chat/save",
                        json={
                            'message': answer,
                            'type': 'bot'
                        },
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        timeout=5
                    )
                    print(f"Save bot message response: {save_resp2.status_code}")
            except Exception as e:
                print(f"Error saving to backend: {e}")
        
        # If no local results, try the Node.js backend as fallback
        if not search_results:
            token = request.session.get('token')
            if token:
                try:
                    response = requests.post(
                        f"{NODE_API}/chat/message",
                        json={'message': message},
                        headers={'Authorization': f'Bearer {token}'},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('response'):
                            answer = data['response']
                except Exception as e:
                    print(f"Backend API error: {e}")
        
        return JsonResponse({
            'success': True,
            'message': answer,
            'sources': [r['source'] for r in search_results] if search_results else []
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        print(f"Error processing message: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_conversations(request):
    """
    Get list of user's conversations
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # Try to get conversations from backend
        response = requests.get(
            f"{NODE_API}/chat/conversations",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'conversations': []})
            
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return JsonResponse({'conversations': []})


def get_conversation_history(request, conversation_id):
    """
    Get history for a specific conversation
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        response = requests.get(
            f"{NODE_API}/chat/conversations/{conversation_id}",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'messages': []})
            
    except Exception as e:
        print(f"Error getting conversation history: {e}")
        return JsonResponse({'messages': []})
