import json
from django.http import JsonResponse
from mail.models import Email, PGPKey, EmailPGPKey
from django.conf import settings
from ..utils.pgp_encryption import decrypt_message, decrypt_and_verify_message, verify_message
from ..utils.hmac_auth import verify_hmac


def get_email(request, id, email):
    if email.signed:
        email_pgp_key = EmailPGPKey.objects.filter(email=id).first()
        if email_pgp_key is None:
            return JsonResponse({'error': 'Email PGP key not found.'}, status=400)
        
        msg = verify_message(email.body, email_pgp_key.sender_public_key.public_key)
        if msg.get('error') is not None:
            return JsonResponse({'error': f'Failed to decrypt message: {msg.get("error")}'}, status=400)
            
        email.body = msg
    
    return JsonResponse(email.serialize())


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
            email_pgp_key = EmailPGPKey.objects.filter(email=email_id).first()
            if email_pgp_key is None:
                return JsonResponse({'error': 'Email PGP key not found.'}, status=400)
            
            if passphrase != user_pgp_key.passphrase:
                return JsonResponse({'error': 'Passphrase does not match.'}, status=400)
            
            if email.encrypted and email.signed:
                decrypted_body = decrypt_and_verify_message(email.body, user_pgp_key.private_key, passphrase, email_pgp_key.sender_public_key.public_key)
            elif email.encrypted:            
                decrypted_body = decrypt_message(email.body, user_pgp_key.private_key, passphrase)
            elif email.signed:
                decrypted_body = verify_message(email.body, email_pgp_key.sender_public_key.public_key) 
            
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