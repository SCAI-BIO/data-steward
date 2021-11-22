import json

import requests
from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .models import CustomUser
from datastewardbackend.views import use_token_auth
from rest_framework.decorators import api_view,  permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib import messages
from djoser.conf import settings

def login_html_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        next = request.POST.get('redirect')
        
        
        response = requests.post(url=django_settings.BASE_HTTP_URL + "auth/token/login/", data={'username': username, 'password': password})
        
        if(response.status_code == 400):
            messages.error(request, 'Username or password incorrect.')
            return render(request, "login.html") 
        user = CustomUser.objects.get(username=username)
        if not user.is_verified:
            messages.error(request, 'Your user is not veriefied yet. In urgend cases write an email to philipp.wegner@scai.fraunhofer.de')
            return render(request, "login.html") 
        t = json.loads(response.text)['auth_token']
        http_response = HttpResponseRedirect(next)
        
        days_expire = 30
        http_response.set_cookie("idsn_access_token", t, days_expire * 24 * 60 * 60, httponly=True)
        return http_response

    else:
        return render(request, "login.html") 

@require_http_methods(['POST'])
def register(request):
    data = request.POST
    username = data['username']
    reason = data['reason']
    affiliation = data['affiliation']
    password = data['password1']
    #print(f"user created with {username}{password}")
    user = CustomUser.objects.create_user(username, username, password)
    user.affiliation = affiliation
    user.reason = reason 
    user.save()
    messages.info(request, "You successfully signed up for the IDSN Services. A memeber of our team will verify your registration in the next few days! In urgend cases please Mail: philipp.wegner@scai.fraunhofer.de")
    return render(request, "login.html")



@require_http_methods(['GET'])
def user_is_logged_in(request):
    token = request.GET.get("token")
    if settings.TOKEN_MODEL.objects.filter(key=token).exists():
        print("token")
        return JsonResponse({"message": "authorized"})
    else:
        print("not authorized")
        return JsonResponse({"message": "not authorized"})

    
    

    
