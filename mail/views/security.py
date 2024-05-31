import json
import logging
import pgpy
from datetime import datetime, timedelta
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
from django.http import JsonResponse
from mail.models import PGPKey, ReceivedPublicKey

logger = logging.getLogger('app_api') #from LOGGING.loggers in settings.py


def user_keys(request):
    if request.method == 'GET':
        try:
            pgp_keys = PGPKey.objects.filter(user=request.user).only('key_id', 'expire_date', 'encrypt', 'sign', 'key_size', 'default_key', 'created')
            return JsonResponse([key.serialize_public() for key in pgp_keys], safe=False)
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP keys not found.'}, status=404)
    else:
        return JsonResponse({
            'error': 'GET request required.'
        }, status=400)


def user_key_item(request, key_id):
    if request.method == 'GET':
        try:
            pgp_key = PGPKey.objects.get(user=request.user, key_id=key_id)
            return JsonResponse(pgp_key.serialize_detail())
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP key not found.'}, status=404)
        
    elif request.method == 'DELETE':
        try:
            pgp_key = PGPKey.objects.get(user=request.user, key_id=key_id)
            pgp_key.delete()
            return JsonResponse({'message': 'PGP key deleted successfully.'})
        except PGPKey.DoesNotExist:
            return JsonResponse({'error': 'PGP key not found.'}, status=404)
        
    else:
        return JsonResponse({
            'error': 'GET or DELETE request required.'
        }, status=400)
        
        
def received_keys(request):
    if request.method == 'GET':
        try:
            keys = ReceivedPublicKey.objects.filter(user=request.user)
            return JsonResponse([key.serialize_public() for key in keys], safe=False)
        except ReceivedPublicKey.DoesNotExist:
            return JsonResponse({'error': 'Received keys not found.'}, status=404)
        
    else:
        return JsonResponse({
            'error': 'GET request required.'
        }, status=400)
        

def received_key_item(request, key_id):
    if request.method == 'GET':
        try:
            keys = ReceivedPublicKey.objects.get(user=request.user, key_id=key_id)
            return JsonResponse(keys.serialize_public())
        except ReceivedPublicKey.DoesNotExist:
            return JsonResponse({'error': 'Received keys not found.'}, status=404)
    
    elif request.method == 'DELETE':
        try:
            keys = ReceivedPublicKey.objects.filter(user=request.user, key_id=key_id)
            keys.delete()
            return JsonResponse({'message': 'Received keys deleted successfully.'})
        except ReceivedPublicKey.DoesNotExist:
            return JsonResponse({'error': 'Received keys not found.'}, status=404)
    
    else:
        return JsonResponse({
            'error': 'DELETE request required.'
        }, status=400)


def generate_key(request):
    
    if request.method == 'POST':
        
        data = json.loads(request.body)
        user = request.user
        key_type = data.get('key_type')
        key_size = data.get('key_size')
        expiration = data.get('expire')
        passphrase = data.get('passphrase')
        comment = data.get('comment', '')
        
        if key_type not in ['RSA', 'DSA']:
            return JsonResponse({'error': 'Invalid key type.'}, status=400)
        
        # if key_type == 'ECDSA':
        #     if key_size not in [256, 384, 521]:
        #         return JsonResponse({'error': 'Invalid key size.'}, status=400)
        
        if key_size not in [1024, 2048, 4096]:
            return JsonResponse({'error': 'Invalid key size.'}, status=400)
        
        if not isinstance(expiration, int) or expiration is None:
            return JsonResponse({'error': 'Invalid expiration value.'}, status=400)
        
        key = None
        
        if key_type == 'RSA':
            key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, key_size)
        elif key_type == 'DSA':
            key = pgpy.PGPKey.new(PubKeyAlgorithm.DSA, key_size)
        # elif key_type == 'ECDSA':
        #     key = pgpy.PGPKey.new(PubKeyAlgorithm.ECDSA, key_size)

        # we now have some key material, but our new key doesn't have a user ID yet, and therefore is not yet usable!
        fullname = f'{user.first_name} {user.last_name}'
        uid = pgpy.PGPUID.new(fullname, comment=comment, email=user.email)

        # now we must add the new user id to the key. We'll need to specify all of our preferences at this point
        # because PGPy doesn't have any built-in key preference defaults at this time
        # this example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
        usage_flags = {KeyFlags.Sign, KeyFlags.EncryptCommunications}
        hash_algs = [HashAlgorithm.SHA256]
        symmetric_algs = [SymmetricKeyAlgorithm.AES256]
        compression_algs = [CompressionAlgorithm.ZLIB]    
        
        key.add_uid(
            uid, 
            usage=usage_flags,
            hashes=hash_algs,
            ciphers=symmetric_algs,
            compression=compression_algs,
            key_expiration=timedelta(days=expiration)
        )
        
        key.protect(passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
        
        encrypt = False
        sign = False
        
        if key_type == 'RSA':
            encrypt = True
            sign = True
        elif key_type == 'DSA':
            sign = True
        
        default_key = False
        count_keys = PGPKey.objects.filter(user=user).count()
        if count_keys == 0:
            default_key = True
        
        try:
            pgp_key = PGPKey.objects.create(
                key_id=str(key.fingerprint),
                user=user, 
                public_key=str(key.pubkey), 
                private_key=str(key),
                key_size=key_size,
                encrypt=encrypt,
                sign=sign,
                passphrase=passphrase, 
                expire_date=datetime.now() + timedelta(days=expiration), 
                default_key=default_key,
                created=datetime.now()
            )
            pgp_key.save()
            
            return JsonResponse({'message': 'PGP key generated successfully.'}, status=201)
        except Exception as e:
            logger.error(f'Failed to save PGP key: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)
        
    else:
        return JsonResponse({
            'error': 'POST request required.'
        }, status=400)