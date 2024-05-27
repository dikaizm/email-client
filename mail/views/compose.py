import json
from django.http import JsonResponse

from mail.models import Email, PGPKey, User
from mail.utils import encrypt_message, encrypt_and_sign_message, check_password


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
    if check_password(passphrase, sender_key.passphrase) is False:
        return JsonResponse({'error': 'Passphrase does not match'}, status=400)
    
    sender_private_key = sender_key.private_key
    
    encrypted_bodies = {}
    if is_encrypt and is_sign:
        for user in recipients:
            try:
                pgp_key = PGPKey.objects.get(user=user)
            except PGPKey.DoesNotExist:
                return JsonResponse({'error': f'PGP key for user {user.email} not found!'}, status=400)
            
            try:
                # encrypt_body = encrypt_message(body, pgp_key.public_key)
                encrypt_and_sign_body = encrypt_and_sign_message(body, sender_private_key, pgp_key.public_key, passphrase)
            except ValueError:
                return JsonResponse({'error': f'Failed to encrypt message for user {user.email}.'}, status=400)

            encrypted_bodies[user] = encrypt_and_sign_body


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
            read=(user == request.user)
        )
        emails_to_save.append(email)
    
    # Bulk create emails
    Email.objects.bulk_create(emails_to_save)
    
    # Create recipient relationships
    for email in emails_to_save:
        email.recipients.set(recipients)

    return JsonResponse({'message': 'Email sent successfully.'}, status=201)