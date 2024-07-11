from django import forms
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from ..services import auth

from mail.models import User, UserOAuthToken
from mail.services.auth_google import (
    GoogleSdkLoginFlowService,
)


class GoogleLoginRedirectApi(View):
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleSdkLoginFlowService()

        authorization_url, state = google_login_flow.get_authorization_url()

        request.session["google_oauth2_state"] = state

        return redirect(authorization_url)


class GoogleLoginApi(View):
    class InputValidationForm(forms.Form):
        code = forms.CharField(required=False)
        error = forms.CharField(required=False)
        state = forms.CharField(required=False)

    def get(self, request, *args, **kwargs):
        input_form = self.InputValidationForm(data=request.GET)

        if not input_form.is_valid():
            return

        validated_data = input_form.cleaned_data

        code = validated_data["code"] if validated_data.get("code") != "" else None
        error = validated_data["error"] if validated_data.get("error") != "" else None
        state = validated_data["state"] if validated_data.get("state") != "" else None

        if error is not None:
            return render(request, 'login.html', {'message': error})

        if code is None or state is None:
            return render(request, 'login.html', {'message': 'Code and state are required.'})

        session_state = request.session.get("google_oauth2_state")

        if session_state is None:
            return render(request, 'login.html', {'message': 'CSRF check failed.'})

        del request.session["google_oauth2_state"]

        if state != session_state:
            return render(request, 'login.html', {'message': 'CSRF check failed.'})

        google_login_flow = GoogleSdkLoginFlowService()

        google_tokens = google_login_flow.get_tokens(code=code, state=state)

        id_token_decoded = google_tokens.decode_id_token()
        user_info = google_login_flow.get_user_info(google_tokens=google_tokens)

        user_email = id_token_decoded["email"]
        user = User.get_user_by_email(user_email)
        if user is None:
            return render(request, 'login.html', {'message': 'User not found.'})

        # Check if oauth token already exists
        oauthToken = UserOAuthToken.get_token(user)
        if oauthToken is not None:
            # Update OAuth token
            oauthToken.update_token(user, google_tokens.payload_token)
        else:
            # Save OAuth token
            UserOAuthToken.create_token(user, google_tokens.payload_token)
            
        # Activate user if successfully authenticated
        user.activate_user()

        return render(request, 'login.html', {'message': 'User registered successfully.', 'success': True})

        # user = authenticate(request, username=user_email, is_active=True)
        # login(request, user)
        
        # result = {
        #     "id_token_decoded": id_token_decoded,
        #     "user_info": user_info,
        # }

        # Save cookie for user email
        # response = redirect("index")
        # response = auth.save_cookie(response, 'user_email', user_email)

        # return response