from django.db import IntegrityError
from mail.models import User
from mail.utils.response import ServiceResponse


def register_srv(request):
    fullname = request.POST['fullname']
    if fullname == '':
        return ServiceResponse(success=False, message='Nama lengkap tidak boleh kosong.', status=400).to_dict()
    
    email = request.POST['email']
    password = request.POST['password']
    confirm_password = request.POST['confirm-password']
    
    if password != confirm_password:
        return ServiceResponse(success=False, message='Password tidak sama.', status=400).to_dict()
        
    try:
        split_name = fullname.split(' ')
        first_name = split_name[0]
        # last name from the rest of the name, if split_name has more than 1 element
        last_name = ' '.join(split_name[1:]) if len(split_name) > 1 else ''
        
        user = User.create_user(email, password, first_name=first_name, last_name=last_name, is_active=False)
    except IntegrityError:
        return ServiceResponse(success=False, message='Email sudah terdaftar.', status=400).to_dict()
        
    return ServiceResponse(success=True, message='Registrasi berhasil.', status=200, data=user).to_dict()


def update_password(request, user):
    fullname = request.POST['fullname']
    if fullname == '':
        return ServiceResponse(success=False, message='Nama lengkap tidak boleh kosong.', status=400).to_dict()

    password = request.POST['password']
    confirm_password = request.POST['confirm-password']
    
    if password != confirm_password:
        return ServiceResponse(success=False, message='Password tidak sama.', status=400).to_dict()
        
    user.set_password(password)
    user.save()
    
    return ServiceResponse(success=True, message='', status=200).to_dict()


def save_cookie(response, key, value):
    response.set_cookie(key, value, max_age=60*60*24*7) # Cookie expires in 1 week
    return response