import json

def user_preferences(request):
    """
    Context processor to make user preferences available to all templates
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    default_preferences = {
        'topics': [],
        'notifications': [],
        'language': request.session.get('language', 'en'),
        'theme': request.session.get('theme', 'light')
    }
    
    if not user or not token:
        return {'user_preferences': default_preferences}
    
    # Check for direct session values first (faster - set by save_preferences)
    theme = request.session.get('theme')
    language = request.session.get('language')
    
    if theme or language:
        default_preferences['theme'] = theme if theme else 'light'
        default_preferences['language'] = language if language else 'en'
    
    # Try to get preferences from session (JSON format)
    preferences_json = request.session.get('user_preferences')
    if preferences_json:
        try:
            prefs = json.loads(preferences_json)
            # Merge with defaults
            user_preferences = {**default_preferences, **prefs}
            return {'user_preferences': user_preferences}
        except (json.JSONDecodeError, TypeError):
            pass
    
    return {'user_preferences': default_preferences}