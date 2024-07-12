import json
from django.http import JsonResponse
from mail.models import Email, PGPKey, EmailPGPKey
from django.conf import settings
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
                Email.create_email(
                    user=request.user,
                    key_id=email.id,
                    sender_email=email.sender,
                    recipient_email=email.recipient,
                    subject=email.subject,
                    body=email.plain,
                    label=label,
                    encrypted=False,
                    signed=False
                )
            except Exception as e:
                return JsonResponse({'error': f'Failed to save email: {e}'}, status=400)
        
    return JsonResponse({'success': True, 'message': 'Emails saved.'})


def get_emails(request, label):
    try:
        emails = Email.objects.filter(user=request.user, label=label)
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
        
        try:
            user_pgp_key = PGPKey.objects.get(user=request.user)
            sender_pgp_key = PGPKey.objects.get(user=email.sender)
            
            if sender_pgp_key is None:
                return JsonResponse({'error': 'Email PGP key not found.'}, status=400)
            
            if passphrase != user_pgp_key.passphrase:
                return JsonResponse({'error': 'Passphrase does not match.'}, status=400)
            
            if email.encrypted and email.signed:
                decrypted_body = decrypt_and_verify_message(email.body, user_pgp_key.private_key, passphrase, sender_pgp_key.public_key)
            elif email.encrypted:            
                decrypted_body = decrypt_message(email.body, user_pgp_key.private_key, passphrase)
            elif email.signed:
                decrypted_body = verify_message(email.body, sender_pgp_key.public_key) 
            
            if decrypted_body.get('error') is not None:
                return JsonResponse({'error': f'Failed to decrypt message: {decrypted_body.get("error")}'}, status=400)
            
            # Split body and HMAC key (body::hmac)
            split_body = decrypted_body.get('message').split('::')
            body = split_body[0]
            hmac = split_body[1]
            
            # Verify HMAC authentication
            secret_key = settings.SECRET_KEY
            if verify_hmac(body, secret_key, received_hmac=hmac) is False:
                return JsonResponse({'error': 'Failed to verify HMAC authentication'})
            
            email.body = body
            
            return JsonResponse({'data': email.serialize()})
        
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP key not found.'}, status=400)
    
    else:
        return JsonResponse({
            'error': 'POST request required.'
        }, status=400)