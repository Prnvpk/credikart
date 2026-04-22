from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser


# 🔹 Register
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST['user_type']

        # create user
        CustomUser.objects.create_user(
            username=username,
            password=password,
            user_type=user_type
        )

        return redirect('login')

    return render(request, 'accounts/register.html')


# 🔹 Login
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})

    return render(request, 'accounts/login.html')


# 🔹 Logout
def user_logout(request):
    logout(request)
    return redirect('login')


# 🔹 Dashboard
def dashboard(request):
    return render(request, 'accounts/dashboard.html')