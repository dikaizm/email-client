import json
import gnupg
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .utils import encrypt_message, decrypt_message
from .models import User, Email, PGPKey, UserPublicKey, EmailPublicKey

gpg = gnupg.GPG()

def index(request):
    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, 'inbox.html')

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse('login'))


def login_view(request):
    if request.method == 'POST':

        # Attempt to sign user in
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'login.html', {
                'message': 'Invalid email and/or password.'
            })
    else:
        return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    if request.method == 'POST':
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'register.html', {
                'message': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'register.html', {
                'message': 'Email address already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'register.html')


@csrf_exempt
@login_required
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
    
    encrypted_bodies = {}
    if is_encrypt:
        for user in recipients:
            try:
                pgp_key = PGPKey.objects.get(user=user)
            except PGPKey.DoesNotExist:
                return JsonResponse({'error': f'PGP key for user {user.email} not found!'}, status=400)
            
            try:
                encrypt_body = encrypt_message(body, pgp_key.public_key)
            except ValueError:
                return JsonResponse({'error': f'Failed to encrypt message for user {user.email}.'}, status=400)

            encrypted_bodies[user] = encrypt_body


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


@login_required
def mailbox(request, mailbox):

    # Filter emails returned based on mailbox
    if mailbox == 'inbox':
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=False
        )
    elif mailbox == 'sent':
        emails = Email.objects.filter(
            user=request.user, sender=request.user
        )
    elif mailbox == 'archive':
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=True
        )
    else:
        return JsonResponse({'error': 'Invalid mailbox.'}, status=400)

    # Return emails in reverse chronologial order
    emails = emails.order_by('-timestamp').all()
    return JsonResponse([email.serialize() for email in emails], safe=False)


@csrf_exempt
@login_required
def email(request, email_id):

    # Query for requested email
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except Email.DoesNotExist:
        return JsonResponse({'error': 'Email not found.'}, status=404)

    # Return email contents
    if request.method == 'GET':
        # Hide email body if email is encrypted
        if email.encrypted:
            email.body = ''
        
        return JsonResponse(email.serialize())

    # Update whether email is read or should be archived
    elif request.method == 'PUT':
        data = json.loads(request.body)
        if data.get('read') is not None:
            email.read = data['read']
        if data.get('archived') is not None:
            email.archived = data['archived']
        email.save()
        return HttpResponse(status=204)

    # Email must be via GET or PUT
    else:
        return JsonResponse({
            'error': 'GET or PUT request required.'
        }, status=400)


@csrf_exempt
@login_required
def decrypt(request, email_id):
    
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except:
        return JsonResponse({'error': 'Email not found.'}, status=404)
    
    if request.method == 'GET':
        if not email.encrypted:
            return JsonResponse({'error': 'Email is not encrypted.'}, status=400)
        
        try:
            pgp_key = PGPKey.objects.get(user=request.user)
            decrypted_body = decrypt_message(email.body, pgp_key.private_key, pgp_key.passphrase)
            if decrypted_body == ValueError:
                return JsonResponse({'error': 'Failed to decrypt message.'}, status=400)
            
            return JsonResponse({'decrypted_body': decrypted_body})
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP key not found.'}, status=400)
    
    else:
        return JsonResponse({
            'error': 'GET request required.'
        }, status=400)


@csrf_exempt
@login_required
def manage_pgp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user
        user.pgp_key = data.get('pgp_key')
        user.save()
        return JsonResponse({'message': 'PGP key saved successfully.'}, status=201)
    elif request.method == 'GET':
        return JsonResponse({'pgp_key': request.user.pgp_key})
    else:
        return JsonResponse({
            'error': 'GET or POST request required.'
        }, status=400)