import base64
import json
from django.http import JsonResponse
from urllib import parse

import pgpy
from pgpy.errors import PGPDecryptionError
import requests

from mail.models import PGPKey, User
from mail.utils.response import ServiceResponse
from mail.services.auth_google import oauth_get_credentials
from googleapiclient.discovery import build
from mail.services.pgp_encrypt import PGPEncrypt


'''
Compose email with encryption and signing
'''
def compose2(request):
    # Check recipient emails
    data = json.loads(request.body)
    
    recipient_emails = [email.strip() for email in data.get('recipients').split(',')]
    if recipient_emails == ['']:
        return JsonResponse({
            'success': False,
            'error': 'At least one recipient required.'
        }, status=400)
    
    # Convert email addresses to users
    recipients = convert_recipients_to_users(request.user.email, recipient_emails)
    if not recipients.success:
        return JsonResponse({
            'success': recipients.success,
            'error': recipients.error
        }, status=recipients.status)
    
    oauth_creds = oauth_get_credentials(request.user)
    
    subject = data.get('subject', '')
    body = data.get('body', '')
    is_encrypt = data.get('encrypt', False)
    is_sign = data.get('sign', False)
    passphrase = data.get('passphrase', '')
    
    print(passphrase)
    
    if is_sign:
        # Check passphrase validity
        unlock_res = unlock_key(request.user, passphrase)
        if not unlock_res.success:
            return JsonResponse({
                'success': unlock_res.success,
                'error': unlock_res.error
            }, status=unlock_res.status)
            
    
    for recipient in recipients.data:
        if is_encrypt or is_sign:
            res_encrypt_body = encrypt_sign_body(request.user, recipient, body, is_encrypt, is_sign)
            
            if not res_encrypt_body.success:
                return JsonResponse({
                    'success': res_encrypt_body.success,
                    'error': res_encrypt_body.error
                }, status=res_encrypt_body.status)
                
            body = res_encrypt_body.data
            
        # Compose email content
        mail_content = mail_send(recipient, subject, body)
        send_email(oauth_creds, mail_content)
        print(f"Email sent to {recipient.email}")
        
        
    return JsonResponse({'success': True, 'message': 'Email send successfully'}, status=200)


def mail_send(recipient, subject, body):
    message = {
        'raw': base64.urlsafe_b64encode(
            f'MIME-Version: 1.0\n'
            f'Content-type: text/plain\n; charset=UTF-8\n'
            f'To: {recipient.email}\n'
            f'Subject: {subject}\n\n'
            f'{body}'.encode("utf-8")
        ).decode("utf-8")
    }
    
    return message


def send_email(creds, message):
    service = build('gmail', 'v1', credentials=creds)
    try:
        message = service.users().messages().send(userId='me', body=message).execute()
        return ServiceResponse(success=True, data=message)
    except Exception as e:
        return ServiceResponse(success=False, error=str(e), status=500)


'''
Helper functions
'''
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
        
        if key.is_expired():
            return ServiceResponse(success=False, error=f'PGP key for user {email} has expired!', status=400)
        
        # If recipient has a public key, return key
        if key:
            return ServiceResponse(success=True, data=key.public_key, status=200)
    
    # Else, find public key in keyserver
    encoded_email = parse.quote(email)
    # Send GET request to keyserver
    open_pgp_res = requests.get(f"https://keys.openpgp.org/vks/v1/by-email/{encoded_email}")
    # If public key is found, return key
    if open_pgp_res.status_code == 200:
        return ServiceResponse(success=True, data=open_pgp_res.text, status=200)
    
    # Else, return None
    return ServiceResponse(success=False, error='Public key not found.', status=404)


def encrypt_sign_body(sender: User, recipient: User, body: str, encrypt: bool, sign: bool)-> ServiceResponse:
    # Get sender's key pair
    sender_key = PGPKey.objects.filter(user=sender, default_key=True).first()
    if not sender_key:
        return ServiceResponse(success=False, error='Sender does not have a PGP key.', status=400)
    
    # Get recipient's key pair
    recipient_key = PGPKey.objects.filter(user=recipient, default_key=True).first()
    if not recipient_key:
        return ServiceResponse(success=False, error='Recipient does not have a PGP key.', status=400)
    
    pgp_service = PGPEncrypt(
        s_private_key=sender_key.private_key,
        s_public_key=sender_key.public_key,
        s_passphrase=sender_key.passphrase,
        r_private_key=recipient_key.private_key,
        r_public_key=recipient_key.public_key,
        r_passphrase=recipient_key.passphrase,
    )
    
    if encrypt and sign:
        # encrypt body
        print(f"Encrypting email body to {recipient.email}")
        new_body = pgp_service.encrypt_and_sign_message(body)
    elif encrypt:
        # encrypt body
        print(f"Encrypting email body to {recipient.email}")
        new_body = pgp_service.encrypt_message(body)
    elif sign:
        # sign body
        print(f"Signing email body to {recipient.email}")
        new_body = pgp_service.sign_message(body)
    
    # If new body is an error, return error
    if isinstance(new_body, ValueError):
        return ServiceResponse(success=False, error=str(new_body), status=400)
    
    # Convert to base64
    json_body = json.dumps({
        'body': new_body,
        'public_key': sender_key.public_key
    })
    base64_body = base64.b64encode(json_body.encode()).decode()
        
    return ServiceResponse(success=True, data=base64_body, status=200)


def unlock_key(user, passphrase):
    try:
        key = PGPKey.objects.get(user=user, default_key=True)
    except PGPKey.DoesNotExist:
        return ServiceResponse(success=False, error='Key not found.', status=404)

    priv_key, _ = pgpy.PGPKey.from_blob(key.private_key)
    
    try:
        with priv_key.unlock(passphrase):
            print(f"Key unlocked for {user.email}")
            return ServiceResponse(success=True, data=priv_key, status=200)
    except PGPDecryptionError as e:
        print(f"Failed to unlock key for {user.email}")
        return ServiceResponse(success=False, error=str(e), status=400)