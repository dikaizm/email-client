import json
from django.http import JsonResponse
from urllib import parse

import requests

from mail.models import PGPKey, User
from mail.utils.response import ServiceResponse


def compose2(request):
    # Check recipient emails
    data = json.loads(request.body)
    
    recipient_emails = [email.strip() for email in data.get('recipients').split(',')]
    if recipient_emails == ['']:
        return JsonResponse({
            'error': 'At least one recipient required.'
        }, status=400)
    
    # Convert email addresses to users
    recipients = convert_recipients_to_users(request.user.email, recipient_emails)
    if not recipients.success:
        return JsonResponse({
            'error': recipients.error
        }, status=recipients.status)
    
    subject = data.get('subject', '')
    body = data.get('body', '')
    is_encrypt = data.get('encrypt', False)
    
    return JsonResponse({'error': 'Not implemented.'}, status=501)


def convert_recipients_to_users(user_email: str, recipient_emails: list) -> ServiceResponse:
    recipients = []
    for email in recipient_emails:
        if email == user_email:
            return ServiceResponse(success=False, error='Cannot send email to self.', status=400)
        try:
            user = User.objects.get(email=email)    
            recipients.append(user)
        except User.DoesNotExist:
            return ServiceResponse(success=False, error=f'User with email {email} not found.', status=404)
    return ServiceResponse(success=True, data=recipients)


def is_recipient_has_pubkey(email: str) -> ServiceResponse:
    # Check if input is a valid email
    if '@' not in email:
        return ServiceResponse(success=False, error='Invalid email.', status=400)
    
    # Check if recipient is a user
    recipient = User.objects.filter(email=email).first()
    
    if recipient:    
        # Check if recipient has a public key in the database
        key = PGPKey.objects.filter(user=recipient).first()
        
        # If recipient has a public key, return key
        if key:
            pubkey = key.public_key
            return ServiceResponse(success=True, data=pubkey, status=200)
    
    # Else, find public key in keyserver
    encoded_email = parse.quote(email)
    # Send GET request to keyserver
    open_pgp_res = requests.get(f"https://keys.openpgp.org/vks/v1/by-email/{encoded_email}")
    # If public key is found, return key
    if open_pgp_res.status_code == 200:
        pubkey = open_pgp_res.text
        return ServiceResponse(success=True, data=pubkey, status=200)
    
    # Else, return None
    return ServiceResponse(success=False, error='Public key not found.', status=404)