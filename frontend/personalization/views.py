from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


def personalization(request):
    """
    Personalization page - requires authentication
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        messages.warning(request, "Please log in to access personalization.")
        return redirect('login')
    
    # Get saved preferences from session
    preferences_json = request.session.get('user_preferences', '{}')
    try:
        user_preferences = json.loads(preferences_json)
    except:
        user_preferences = {
            'topics': [],
            'notifications': [],
            'language': 'en',
            'theme': 'light'
        }
    
    return render(request, 'personalization/personalization.html', {
        'user': user,
        'user_preferences': user_preferences,
    })


@require_http_methods(["POST"])
def save_preferences(request):
    """
    Save user preferences to session
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        messages.warning(request, "Please log in to save preferences.")
        return redirect('login')
    
    try:
        # Handle form submission
        topics = request.POST.getlist('topics')
        notifications = request.POST.getlist('notifications')
        language = request.POST.get('language', 'en')
        theme = request.POST.get('theme', 'light')
        
        data = {
            'topics': topics,
            'notifications': notifications,
            'language': language,
            'theme': theme
        }
        
        request.session['user_preferences'] = json.dumps(data)
        request.session.modified = True
        
        messages.success(request, "Preferences saved successfully!")
        
    except Exception as e:
        messages.error(request, f"Error saving preferences: {str(e)}")
    
    return redirect('personalization')
