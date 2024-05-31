import json
from django.http import JsonResponse
from django.conf import settings
from mail.models import Email, PGPKey, User, EmailHMAC, ReceivedPublicKey, EmailPGPKey
from mail.utils.pgp_encryption import encrypt_message, encrypt_and_sign_message, sign_message
from mail.utils.hmac_auth import generate_hmac


def compose(request):
    # Composing a new email must be via POST
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required.'}, status=400)

    # Check recipient emails
    data = json.loads(request.body)
    emails = [email.strip() for email in data.get('recipients').split(',')]
    if emails == ['']:
        return JsonResponse({
            'error': 'At least one recipient required.'
        }, status=400)


    # Convert email addresses to users
    recipients = []
    for email in emails:
        try:
            user = User.objects.get(email=email)    
            recipients.append(user)
        except User.DoesNotExist:
            return JsonResponse({
                'error': f'User with email {email} does not exist.'
            }, status=400)

    # Get contents of email
    subject = data.get('subject', '')
    body = data.get('body', '')
    is_encrypt = data.get('encrypt', False)
    is_sign = data.get('sign', False)
    passphrase = data.get('passphrase', '')
    
    sender_key = PGPKey.objects.filter(user=request.user, default_key=True).first()
    
    # Check passphrase validity
    if is_sign and (passphrase != sender_key.passphrase):
        return JsonResponse({'error': 'Passphrase does not match'}, status=400)    
    
    secret_key = settings.SECRET_KEY
    # Generate HMAC for email
    hmac_body = generate_hmac(body, secret_key)
    combined_body = f'{body}::{hmac_body}'
    
    # Encrypt and/or sign email
    encrypted_bodies = {}
    public_keys_to_save = []
    
    if is_encrypt or is_sign:
        for user in recipients:
            try:
                recipient_key = PGPKey.objects.get(user=user)
                pub_key = ReceivedPublicKey(
                    user=request.user,
                    owner=user,
                    key_id=recipient_key.key_id,
                    public_key=recipient_key.public_key,
                    expire_date=recipient_key.expire_date
                )
                public_keys_to_save.append(pub_key)
                
            except PGPKey.DoesNotExist:
                return JsonResponse({'error': f'PGP key for user {user.email} not found!'}, status=400)
            
            if is_encrypt and is_sign:
                secured_body = encrypt_and_sign_message(combined_body, recipient_key.public_key, sender_key.private_key, passphrase)
            elif is_encrypt:
                secured_body = encrypt_message(combined_body, recipient_key.public_key)
            elif is_sign:
                secured_body = sign_message(combined_body, sender_key.private_key, passphrase)
           
            if isinstance(secured_body, ValueError):
                return JsonResponse({'error': f'Failed to encrypt message for user {user.email}: {str(secured_body)}'}, status=400)

            encrypted_bodies[user] = secured_body


    # Create and save email objects
    all_users = set(recipients)
    all_users.add(request.user)
    
    emails_to_save = []
    for user in all_users:
        email_body = encrypted_bodies[user] if is_encrypt and user in encrypted_bodies else body
        email = Email(
            user=user,
            sender=request.user,
            subject=subject,
            body=email_body,
            read=(user == request.user),
            encrypted=is_encrypt,
        )
        emails_to_save.append(email)
    
    # Bulk create emails
    Email.objects.bulk_create(emails_to_save)
    ReceivedPublicKey.objects.bulk_create(public_keys_to_save)
    
    # Create recipient relationships
    for email in emails_to_save:
        email.recipients.set(recipients)
    
    hmacs_to_save = []
    email_pgpkeys_to_save = []
    if is_encrypt:
        for email in emails_to_save:
            original_msg = body
            email_body = encrypted_bodies[email.user] if email.user in encrypted_bodies else original_msg
            hmac_record = EmailHMAC(email=email, hmac=hmac_body, secret_key=secret_key)
            hmacs_to_save.append(hmac_record)
            
            for public_key in public_keys_to_save:
                email_pgpkey = EmailPGPKey(email=email, recipient_public_key=public_key, sender_private_key=sender_key)
                email_pgpkeys_to_save.append(email_pgpkey)
            
        # Bulk create HMACs
        EmailHMAC.objects.bulk_create(hmacs_to_save)
        
        # Bulk create Email PGP Keys
        EmailPGPKey.objects.bulk_create(email_pgpkeys_to_save)
    

    return JsonResponse({'message': 'Email sent successfully.'}, status=201)