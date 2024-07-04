import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.urls import reverse

from mail.services import auth
from ..models import User
from ..forms import auth as auth_forms


def login_service(request):
    if request.method == 'POST':
        form = auth_forms.LoginForm(request.POST)

        if not form.is_valid():
            return render(request, 'login.html', {
                'message': form
            }, status=400)

        # Attempt to sign user in
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        user = User.get_user_by_email(email)
        if user is None:
            # Register new user
            register_res = auth.register_srv(request)
            if not register_res['success']:
                return render(request, 'login.html', {
                    'message': register_res['message']
                }, status=register_res['status'])
                
            user = register_res['data']
            
            # Redirect to google oauth2 login
            return redirect(reverse('google-login-redirect'))
        elif not user.is_active:
            auth.update_password(request, user)
            return redirect(reverse('google-login-redirect'))
        
        # Attempt to authenticate user
        user = authenticate(request, username=email, password=password, is_active=True)

        # Check if authentication successful
        if user is not None:
            # Show page confirmation of email client configuration
            '''
                incoming server | protocol | security
                outgoing server | protocol | security
                username/email
            '''
                
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
    
    
def email_validation_srv(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        email = data.get('email')
        user = User.get_user_by_email(email)
        
        if user is not None and user.is_active:
            return JsonResponse({
                'message': 'Email sudah terdaftar. Silahkan login.',
                'data': {
                    'is_registered': True,
                }
            }, status=200)
        else:
            return JsonResponse({
                'message': 'Email belum terdaftar di sistem kami. Silahkan daftar.',
                'data': {
                    'is_registered': False,
                }
            }, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)