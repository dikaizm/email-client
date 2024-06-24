import json
import logging
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ..models import Email
from .security import generate_key, user_keys, user_key_item, received_keys, received_key_item
from .compose import compose, request_key
from .auth import login_service, register_service
from .email import get_email, decrypt_email


logger = logging.getLogger('app_api') #from LOGGING.loggers in settings.py

def index(request):
    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, 'inbox.html')

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse('login'))


def login_view(request):
    return login_service(request)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register_view(request):
    return register_service(request)


@csrf_exempt
@login_required
def compose_view(request):
    return compose(request)


@csrf_exempt
@login_required
def request_key_view(request):
    return request_key(request)


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
        return get_email(request, email_id, email)

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


# POST request to generate a new PGP key
# Request body: { key_type, key_size, expiration, passphrase, comment }
@csrf_exempt
@login_required
def generate_key_view(request):
    return generate_key(request)


@csrf_exempt
@login_required
def user_keys_view(request):
    return user_keys(request)


@csrf_exempt
@login_required
def user_key_item_view(request, key_id):
    return user_key_item(request, key_id)


@csrf_exempt
@login_required
def received_keys_view(request):
    return received_keys(request)


@csrf_exempt
@login_required
def received_key_item_view(request, key_id):
    return received_key_item(request, key_id)


@csrf_exempt
@login_required
def decrypt_email_view(request, email_id):
    return decrypt_email(request, email_id)