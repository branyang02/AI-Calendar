from django.shortcuts import render, redirect
from django.contrib.auth import logout

# Create your views here.
def signin(request):
    return render(request, "oauth_app/signin.html")

def logout_view(request):
    logout(request)
    return redirect("/")