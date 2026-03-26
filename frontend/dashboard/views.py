from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import requests

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
        response = requests.get(f"{NODE_API}/dashboard/", headers=headers, timeout=5)
        if response.status_code == 200:
            dashboard_data = response.json().get('data', {})
        else:
            messages.warning(request, "Failed to fetch dashboard data.")
            dashboard_data = {}
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error fetching dashboard data: {str(e)}")
        dashboard_data = {}
    
    context = {
        'user': user,
        'is_admin': False,
        'dashboard_data': dashboard_data
    }
    return render(request, 'dashboard/dashboard.html', context)


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
