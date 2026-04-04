from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import requests
from datetime import datetime

NODE_API = "http://localhost:7001/api"


def dashboard(request):
    """
    Display dashboard based on user role.
    Admins see admin dashboard; regular users see user dashboard.
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        messages.warning(request, "Please log in to access the dashboard.")
        return redirect('login')
    
    # Admin dashboard
    if user.get('role', 'user').lower() == 'admin':
        return admin_dashboard(request, user, token)
    
    # Regular user dashboard
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Fetch dashboard data
        dashboard_data = {}
        try:
            response = requests.get(f"{NODE_API}/dashboard/", headers=headers, timeout=5)
            if response.status_code == 200:
                dashboard_data = response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            messages.warning(request, f"Failed to fetch dashboard data: {str(e)}")
        
        # Fetch recent conversations
        recent_queries = []
        try:
            conversations_response = requests.get(f"{NODE_API}/chat/conversations", headers=headers, timeout=5)
            if conversations_response.status_code == 200:
                conversations_data = conversations_response.json()
                # Backend returns list directly, not wrapped in 'data' key
                if isinstance(conversations_data, list):
                    # Get last 5 conversations
                    recent_queries = conversations_data[:5]
                    # Add time_ago field
                    for query in recent_queries:
                        query['time_ago'] = get_time_ago(query.get('updatedAt') or query.get('createdAt'))
                elif isinstance(conversations_data, dict):
                    # Fallback if backend returns dict with 'data' key
                    recent_queries = conversations_data.get('data', [])[:5]
                    for query in recent_queries:
                        query['time_ago'] = get_time_ago(query.get('updatedAt') or query.get('createdAt'))
        except requests.exceptions.RequestException as e:
            messages.warning(request, f"Failed to fetch recent queries: {str(e)}")
        
        # Fetch user preferences
        user_preferences = {'topics': []}
        try:
            preferences_response = requests.get(f"{NODE_API}/preferences/", headers=headers, timeout=5)
            if preferences_response.status_code == 200:
                preferences_data = preferences_response.json()
                if preferences_data.get('success'):
                    user_preferences = preferences_data.get('preferences', {'topics': []})
        except requests.exceptions.RequestException as e:
            messages.warning(request, f"Failed to fetch preferences: {str(e)}")
        
        # Calculate stats from conversations
        total_queries = len(recent_queries)
        favorite_topics = len(user_preferences.get('topics', []))
        active_sessions = 1 if recent_queries else 0
        resolved_queries = total_queries  # Assume all are resolved
        
        context = {
            'user': user,
            'is_admin': False,
            'total_queries': total_queries,
            'favorite_topics': favorite_topics,
            'active_sessions': active_sessions,
            'resolved_queries': resolved_queries,
            'recent_queries': recent_queries,
            'user_preferences': user_preferences
        }
        return render(request, 'dashboard/dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('home')


def admin_dashboard(request, user, token):
    """
    Admin dashboard with CRUD for user management via backend API.
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Handle POST requests (add/edit/delete users)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add':
                data = {
                    'name': request.POST.get('name'),
                    'email': request.POST.get('email'),
                    'password': request.POST.get('password'),
                    'role': request.POST.get('role', 'user')
                }
                resp = requests.post(f"{NODE_API}/dashboard/users/", json=data, headers=headers, timeout=5)
                if resp.status_code == 201:
                    messages.success(request, "User created successfully!")
                else:
                    messages.error(request, f"Error: {resp.json().get('message', 'Failed to create user')}")
            
            elif action == 'edit':
                user_id = request.POST.get('user_id')
                data = {
                    'name': request.POST.get('name'),
                    'email': request.POST.get('email'),
                    'role': request.POST.get('role', 'user')
                }
                password = request.POST.get('password')
                if password:
                    data['password'] = password
                resp = requests.put(f"{NODE_API}/dashboard/users/{user_id}", json=data, headers=headers, timeout=5)
                if resp.status_code == 200:
                    messages.success(request, "User updated successfully!")
                else:
                    messages.error(request, f"Error: {resp.json().get('message', 'Failed to update user')}")
            
            elif action == 'delete':
                user_id = request.POST.get('user_id')
                resp = requests.delete(f"{NODE_API}/dashboard/users/{user_id}", headers=headers, timeout=5)
                if resp.status_code == 200:
                    messages.success(request, "User deleted successfully!")
                else:
                    messages.error(request, f"Error: {resp.json().get('message', 'Failed to delete user')}")
            else:
                messages.warning(request, "Invalid action.")
        
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Server error: {str(e)}")
        
        return redirect('dashboard')

    # GET request: fetch analytics and users from backend
    analytics = {
        'totalUsers': 0,
        'totalQueries': 0,
        'activeSessions': 0,
        'resolvedQueries': 0,
        'newUsersToday': 0
    }
    users = []
    conversations = []
    
    try:
        # Fetch admin analytics
        analytics_resp = requests.get(f"{NODE_API}/admin/", headers=headers, timeout=5)
        if analytics_resp.status_code == 200:
            data = analytics_resp.json()
            api_data = data.get('data', {})
            # Map API fields to template fields
            analytics['totalUsers'] = api_data.get('totalUsers', 0)
            analytics['totalQueries'] = api_data.get('totalQueries', 0)
            analytics['activeSessions'] = api_data.get('activeUsers', 0)
            analytics['resolvedQueries'] = api_data.get('resolvedQueries', 0)
            analytics['newUsersToday'] = api_data.get('newUsersToday', 0)
            conversations = api_data.get('recentConversations', [])

        # Fetch all users
        users_resp = requests.get(f"{NODE_API}/dashboard/users/", headers=headers, timeout=5)
        if users_resp.status_code == 200:
            users_raw = users_resp.json().get('users', [])
            users = [{
                'id_str': str(u.get('_id')),
                'id': u.get('_id'),
                'name': u.get('name'),
                'email': u.get('email'),
                'role': u.get('role', 'user')
            } for u in users_raw]
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error fetching admin data: {str(e)}")

    context = {
        'user': user,
        'is_admin': True,
        'analytics': analytics,
        'users': users,
        'conversations': conversations
    }

    return render(request, 'dashboard/admindashboard.html', context)


def admin_conversations(request):
    """
    API endpoint to get all conversations for admin dashboard.
    """
    user = request.session.get('user')
    token = request.session.get('token')
    
    if not user or not token:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    if user.get('role', 'user').lower() != 'admin':
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{NODE_API}/admin/conversations", headers=headers, timeout=5)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to fetch conversations'}, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_time_ago(date_string):
    """
    Convert a date string to a human-readable time ago format.
    """
    if not date_string:
        return 'Unknown'
    
    try:
        # Parse the date string
        if isinstance(date_string, str):
            # Try different date formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                try:
                    date = datetime.strptime(date_string, fmt)
                    break
                except ValueError:
                    continue
            else:
                return 'Unknown'
        else:
            date = date_string
        
        now = datetime.utcnow()
        diff = now - date
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'
        else:
            return date.strftime('%Y-%m-%d')
    except Exception:
        return 'Unknown'
