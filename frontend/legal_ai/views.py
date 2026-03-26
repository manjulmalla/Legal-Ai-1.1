import requests
from django.shortcuts import render, redirect
from django.contrib import messages

NODE_API = "http://localhost:7001/api"
# -------------------------
# first page view
#--------------------------
def thumbnail(request):
    return render(request, "thumbnail.html")


# -------------------------
# REGISter
# -------------------------
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # password match check
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        data = {
            "name": username,
            "email": email,
            "password": password1
        }

        try:
            response = requests.post(
                f"{NODE_API}/auth/register",
                json=data,
                timeout=5
            )

            res = response.json()

            if response.status_code == 201:
                messages.success(
                    request,
                    "Registration successful! Please login."
                )
                return redirect("login")

            else:
                messages.error(
                    request,
                    res.get("message", "Registration failed")
                )

        except requests.exceptions.ConnectionError:
            messages.error(
                request,
                "Authentication server is not running"
            )

        except requests.exceptions.Timeout:
            messages.error(
                request,
                "Server timeout. Try again later."
            )

    return render(request, "register.html")

# -------------------------
# LOGIN
# -------------------------
def login_view(request):
    if request.method == "POST":
        data = {
            "email": request.POST.get("email"),
            "password": request.POST.get("password"),
        }

        try:
            response = requests.post(
                f"{NODE_API}/auth/login",
                json=data,
                timeout=5
            )

            try:
                res = response.json()
            except ValueError:
                res = {}

            if response.status_code == 200:
                request.session["token"] = res.get("token")
                request.session["user"] = res.get("user")

                return redirect("home")

            else:
                messages.error(
                    request,
                    res.get("message", "Invalid credentials")
                )

        except requests.exceptions.ConnectionError:
            messages.error(request, "Node server not running")
        except requests.exceptions.Timeout:
            messages.error(request, "Node server timeout")

    return render(request, "login.html")
#--------------------
# logout
#--------------------
def logout_view(request):
    request.session.flush()
    return redirect("thumbnail")