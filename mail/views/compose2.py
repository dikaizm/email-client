import base64
import json
import secrets
from django.http import JsonResponse
from urllib import parse

import pgpy
from pgpy.errors import PGPDecryptionError
import requests

from mail.models import Email, EmailHMAC, PGPKey, User
from mail.services.gmail.index import GmailService
from mail.utils.hmac_auth import generate_hmac
from mail.utils.response import ServiceResponse
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
    
        
    subject = data.get('subject', '')
    body = data.get('body', '')
    is_encrypt = data.get('encrypt', False)
    is_sign = data.get('sign', False)
    passphrase = data.get('passphrase', '')
        
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
        email_sent = GmailService(request.user).send_message(
            sender=request.user.email,
            to=recipient.email,
            subject=subject,
            msg_plain=body
        )
        
        print(f"Email sent to {recipient.email}")
        print(email_sent.serialize())

        try:
            Email.create_email(
                key_id=email_sent.id,
                user=request.user,
                sender_email=email_sent.sender,
                recipient_email=email_sent.recipient,
                subject=email_sent.subject,
                body=email_sent.plain,
                encrypted=is_encrypt,
                signed=is_sign,
                label='SENT',
                date=email_sent.date
            )
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to save email: {e}'
            }, status=500)
        
        
    return JsonResponse({'success': True, 'message': 'Email send successfully'}, status=200)


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
            # Create new user
            user = User.objects.create(email=email, username=email, is_active=False)
            recipients.append(user)
            
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
        
        if key is not None and key.is_expired():
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
        recipient_key = is_recipient_has_pubkey(recipient.email)
        if not recipient_key.success:
            return ServiceResponse(success=False, error=recipient_key.error, status=recipient_key.status)
        
        recipient_key.public_key = recipient_key.data
        
    
    pgp_service = PGPEncrypt(
        s_private_key=sender_key.private_key,
        s_public_key=sender_key.public_key,
        s_passphrase=sender_key.passphrase,
        r_public_key=recipient_key.public_key,
    )
    
    # Generate random secret key
    secret_key = secrets.token_hex(16)
    # Generate HMAC auth key
    hmac_body = generate_hmac(body, secret_key)
    
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
        
    print(new_body)
    
    # If new body is an error, return error
    if isinstance(new_body, ValueError):
        return ServiceResponse(success=False, error=str(new_body), status=400)
    
    # Save hmac
    try:
        hmac = EmailHMAC.objects.create(
            hmac=hmac_body,
            secret_key=secret_key,
        )
    except Exception as e:
        return ServiceResponse(success=False, error=f'Failed to save HMAC: {e}', status=500)
    
    if not hasattr(recipient_key, 'fingerprint'):
        recipient_key.fingerprint = ''
    
    # Convert to base64
    json_body = json.dumps({
        'body': new_body,
        'sender_public_key': sender_key.public_key,
        'recipient_key_fpr': recipient_key.fingerprint,
        'hmac_key': f"{hmac.id}::{hmac.hmac}",
    })
    base64_body = base64.b64encode(json_body.encode()).decode()
    # Add text to indicate that the body is encrypted or signed
    base64_body = f'{base64_body}\n-----AYU_OPENPGP-----\nFLAG:{json.dumps({"ENCRYPTED": encrypt, "SIGNED": sign})}'
        
    return ServiceResponse(success=True, data=base64_body, status=200)


def unlock_key(user, passphrase):
    try:
        key = PGPKey.objects.get(user=user, default_key=True)
    except PGPKey.DoesNotExist:
        return ServiceResponse(success=False, error='Private key not found.', status=404)

    priv_key, _ = pgpy.PGPKey.from_blob(key.private_key)
    
    try:
        with priv_key.unlock(passphrase):
            print(f"Key unlocked for {user.email}")
            return ServiceResponse(success=True, data=priv_key, status=200)
    except PGPDecryptionError as e:
        print(f"Failed to unlock key for {user.email}")
        return ServiceResponse(success=False, error=str(e), status=400)