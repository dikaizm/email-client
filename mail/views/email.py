from django.http import JsonResponse


def get_email(request, email):
    # Hide email body if email is encrypted
    # if email.encrypted and (request.user not in email.recipients.all()):
    #     email.body = ''
    
    return JsonResponse(email.serialize())