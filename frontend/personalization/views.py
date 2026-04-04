from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import requests

NODE_API = "http://localhost:7001/api"


def personalization(request):
    """
    Personalization page - requires authentication
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        messages.warning(request, "Please log in to access personalization.")
        return redirect('login')
    
    # Default preferences
    user_preferences = {
        'topics': [],
        'notifications': [],
        'language': 'en',
        'theme': 'light'
    }
    
    # Fetch preferences from backend API
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{NODE_API}/preferences/", headers=headers, timeout=5)
        if response.status_code == 200:
            preferences_data = response.json()
            if preferences_data.get('success'):
                user_preferences = preferences_data.get('preferences', user_preferences)
    except requests.exceptions.RequestException as e:
        messages.warning(request, f"Failed to fetch preferences from server: {str(e)}")
        # Fall back to session preferences if API fails
        preferences_json = request.session.get('user_preferences', '{}')
        try:
            user_preferences = json.loads(preferences_json)
        except:
            pass
    
    return render(request, 'personalization/personalization.html', {
        'user': user,
        'user_preferences': user_preferences,
    })


@require_http_methods(["POST"])
def save_preferences(request):
    """
    Save user preferences to backend API
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
        
        # Save to backend API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{NODE_API}/preferences/",
            json=data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                messages.success(request, "Preferences saved successfully!")
                # Also save to session as backup
                request.session['user_preferences'] = json.dumps(data)
                request.session.modified = True
            else:
                messages.error(request, f"Error saving preferences: {response_data.get('message', 'Unknown error')}")
        else:
            messages.error(request, f"Error saving preferences: Server returned status {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error connecting to server: {str(e)}")
        # Save to session as fallback
        try:
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
            messages.warning(request, "Preferences saved locally (server unavailable)")
        except Exception as inner_e:
            messages.error(request, f"Error saving preferences: {str(inner_e)}")
    
    except Exception as e:
        messages.error(request, f"Error saving preferences: {str(e)}")
    
    return redirect('personalization')
