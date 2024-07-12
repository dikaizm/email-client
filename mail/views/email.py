import base64
import binascii
from datetime import datetime
import json
from django.http import JsonResponse
from mail.models import Email, EmailHMAC, PGPKey, EmailPGPKey, User
from django.conf import settings

from mail.services.pgp_encrypt import PGPEncrypt
from mail.views.compose2 import unlock_key
from ..utils.pgp_encryption import decrypt_message, decrypt_and_verify_message, verify_message
from ..utils.hmac_auth import verify_hmac
from mail.services.gmail.index import GmailService
from mail.services.gmail.query import construct_query


def refresh_emails(request, label):
    gmail = GmailService(request.user)
    labels = gmail.list_labels()
    
    # print(labels)
    
    query_params = {
        "newer_than": (2, "day"),
        "unread": True,
        "labels": [[label]]
    }
    
    try:
        # emails = gmail.get_unread_inbox(labels=[label])
        emails = gmail.get_messages(query=construct_query(query_params))
    except Exception as e:
        return JsonResponse({'error': f'Failed to retrieve emails: {e}'}, status=400)
    
    # Save emails to database
    for email in emails:        
        if email.sender == request.user.email and label == 'INBOX':
            continue
        
        try:
            Email.objects.get(user=request.user, key_id=email.id)
        except Email.DoesNotExist:
            try:
                if email.plain is None:
                    email.plain = ''
                    
                encrypted = False
                signed = False
                body_flags = extract_body_flag(email.plain)
                if body_flags is not None:
                    encrypted = body_flags.get('ENCRYPTED', False)
                    signed = body_flags.get('SIGNED', False)
                
                Email.create_email(
                    user=request.user,
                    key_id=email.id,
                    sender_email=email.sender,
                    recipient_email=email.recipient,
                    subject=email.subject,
                    body=email.plain,
                    label=label,
                    encrypted=encrypted,
                    signed=signed,
                    date=email.date
                )
            except Exception as e:
                return JsonResponse({'error': f'Failed to save email: {e}'}, status=400)
        
    return JsonResponse({'success': True, 'message': 'Emails saved.'})


def get_emails(request, label):
    try:
        emails = Email.objects.filter(user=request.user, label=label).order_by('-date').all()
    except:
        return JsonResponse({'error': 'Email not found.'}, status=404)
    
    emails = [email.serialize() for email in emails]
    return JsonResponse({'success': True, 'message': 'Email retrieved', 'data': {'emails': emails, 'user': request.user.email}})


def decrypt_email(request, email_id):
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except:
        return JsonResponse({'error': 'Email not found.'}, status=404)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        if data is None:
            return JsonResponse({'error': 'Request body required.'}, status=400)
        
        if not email.encrypted:
            return JsonResponse({'error': 'Email is not encrypted.'}, status=400)
        
        passphrase = data.get('passphrase', '')
        
        # Extract body
        payload = extract_body_payload(email.body)
        
        try:
            sender = User.objects.get(email=email.sender_email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Sender not found.'}, status=400)
        
        try:
            recipient_key = PGPKey.objects.get(fingerprint=payload.recipient_key_fpr)
            # sender_key = PGPKey.objects.filter(user=sender, default_key=True).first()
                
            # if sender_key is None:
            #     return JsonResponse({'error': 'Sender email PGP key not found.'}, status=400)
            
            if passphrase != recipient_key.passphrase:
                return JsonResponse({'error': 'Passphrase does not match.'}, status=400)
            
            pgp_service = PGPEncrypt(
                # s_public_key=sender_key.public_key,
                s_public_key=payload.sender_public_key,
                r_private_key=recipient_key.private_key,
                r_public_key=recipient_key.public_key,
                r_passphrase=recipient_key.passphrase,
            )
                        
            if email.encrypted and email.signed:
                decrypted_body = pgp_service.decrypt_and_verify_message(payload.body)
            elif email.encrypted:
                decrypted_body = pgp_service.decrypt_message(payload.body)
            elif email.signed:
                decrypted_body = pgp_service.verify_message(payload.body)
            
            if decrypted_body.get('error') is not None:
                return JsonResponse({'error': f'Failed to decrypt message: {decrypted_body.get("error")}'}, status=400)
            
            email.body = decrypted_body.get('message')
            
            # Split body and HMAC key (body::hmac)
            split_hmac = payload.hmac_key.split('::')
            hmac_id = split_hmac[0]
            hmac_key = split_hmac[1]
            
            # Get HMAC key from database
            try:
                hmac = EmailHMAC.objects.get(pk=hmac_id)
            except EmailHMAC.DoesNotExist:
                return JsonResponse({'error': 'HMAC key not found.'}, status=400)
            
            # Verify HMAC authentication
            if verify_hmac(email.body, hmac.secret_key, received_hmac=hmac_key) is False:
                print("Failed to verify HMAC authentication")
                return JsonResponse({'error': 'Failed to verify HMAC authentication'})

            
            return JsonResponse({'data': email.serialize()})
        
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP key not found.'}, status=400)
    
    else:
        return JsonResponse({
            'error': 'POST request required.'
        }, status=400)
        

def split_body_ayu(body):
    split_body = body.split('-----AYU_OPENPGP-----')
    if len(split_body) < 2:
        return None
    
    return split_body


class BodyPayload:
    def __init__(self, payload: dict):
        # Ensure payload contains necessary keys
        if 'body' not in payload or 'sender_public_key' not in payload or 'recipient_key_fpr' not in payload or 'hmac_key' not in payload:
            raise ValueError("Missing keys in payload")
        
        self.body = payload.get('body')
        self.sender_public_key = payload.get('sender_public_key')
        self.recipient_key_fpr = payload.get('recipient_key_fpr')
        self.hmac_key = payload.get('hmac_key')


def extract_body_payload(body) -> BodyPayload:
    split_body = split_body_ayu(body)
    if split_body is None:
        return None

    # Get the first part of the split body
    payload = split_body[0].strip()
    
    # Decode base64 payload
    try:
        payload = base64.b64decode(payload).decode()
    except binascii.Error:
        print("Invalid base64 in PAYLOAD")
        return None
    
    # Convert payload to JSON
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        print("Invalid JSON in PAYLOAD")
        return None
    
    return BodyPayload(payload_dict)
    

def extract_body_flag(body) -> dict:
    split_body = split_body_ayu(body)
    if split_body is None:
        return None

    # Get the end part of the split body
    flag = split_body[-1].strip()

    # Find the flag line starting with 'FLAG:'
    flag_line = None
    for line in flag.split('\n'):
        if line.startswith('FLAG:'):
            flag_line = line
            break

    # Extract the ENCRYPTED and SIGNED values
    if flag_line:
        # Extract the JSON part from the FLAG line
        json_part = flag_line.replace('FLAG:', '').strip()
        
        try:
            # Parse the JSON part
            flag_dict = json.loads(json_part)

            # Get the values of ENCRYPTED and SIGNED
            encrypted_value = flag_dict.get('ENCRYPTED', False)
            signed_value = flag_dict.get('SIGNED', False)

            print(f"ENCRYPTED: {encrypted_value}")
            print(f"SIGNED: {signed_value}")
        except json.JSONDecodeError:
            print("Invalid JSON in FLAG line")
            return None
    else:
        print("FLAG line not found")
        return None

    return flag_dict