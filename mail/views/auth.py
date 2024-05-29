from django.contrib.auth import authenticate, login
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError
from ..models import User
import urllib


def login_service(request):
    if request.method == 'POST':

        # Attempt to sign user in
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            response = HttpResponseRedirect(reverse('index'))
            # Set cookie with user's email
            response.set_cookie('user_email', user.email, max_age=60*60*24*7) # Cookie expires in 1 week
            return response
        else:
            return render(request, 'login.html', {
                'message': 'Invalid email and/or password.'
            })
    else:
        return render(request, 'login.html')
    
    
def register_service(request):
    if request.method == 'POST':
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'register.html', {
                'message': 'Passwords must match.'
            })

        # Attempt to create new user
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        
        try:
            user = User.objects.create_user(email, email, password, first_name=first_name, last_name=last_name)
            user.save()
        except IntegrityError:
            return render(request, 'register.html', {
                'message': 'Email address already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'register.html')