from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests


NODE_API = "http://localhost:7001/api"

# --------- HOME PAGE ---------
def index(request):
    """
    Render home page with user context.
    Checks if user is authenticated via session, redirects to login if not.
    """
    # Check if user is logged in via session
    user = request.session.get('user')
    if not user:
        return redirect('login')
    
    context = {
        'user': user,
        'token': request.session.get('token', ''),
    }
    return render(request, 'home/index.html', context)


# --------- SEARCH QUESTIONS ---------
def search_questions(request):
    """
    API endpoint to handle search/question submission.
    Stores the question in session and returns response.
    """
    # Check if user is logged in
    if not request.session.get('user'):
        return JsonResponse({
            'status': 'error',
            'message': 'Please login first'
        }, status=401)
    
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        
        if not question:
            return JsonResponse({
                'status': 'error',
                'message': 'Please enter a question'
            }, status=400)
        
        # Store question in session for chatbot to use
        request.session['current_question'] = question
        request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'message': 'Question received',
            'question': question
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)