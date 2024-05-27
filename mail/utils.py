import os
import gnupg
import pgpy
import hmac
import hashlib
from django.conf import settings

gpg = gnupg.GPG()

def encrypt_message(message, public_key):
    # Load public key
    public_key, _ = pgpy.PGPKey.from_blob(public_key)
    
    # Create PGP message
    pgp_message = pgpy.PGPMessage.new(message)
    
    # Encrypt message
    encrypted_message = public_key.encrypt(pgp_message)
    
    return str(encrypted_message)


def decrypt_message(encrypted_message, private_key, passphrase):
    # Load private key
    private_key, _ = pgpy.PGPKey.from_blob(private_key)
    
    # Unlock private key with passphrase
    with private_key.unlock(passphrase):
        # Load encrypted message
        enc_msg = pgpy.PGPMessage.from_blob(encrypted_message)
        decrypt_msg = private_key.decrypt(enc_msg)
        
    return str(decrypt_msg.message)


def sign_message(message, private_key, passphrase):
    # Load the private key
    priv_key, _ = pgpy.PGPKey.from_blob(private_key)
    
    # Unlock the private key with the passphrase
    with priv_key.unlock(passphrase):
        # Create a PGPMessage object from the plaintext message
        pgp_message = pgpy.PGPMessage.new(message)
        
        # Sign the message
        signed_message = priv_key.sign(pgp_message)
    
    return str(signed_message)


def encrypt_and_sign_message(message, recipient_public_key, sender_private_key, passphrase):
    # Load the recipient's public key
    pub_key, _ = pgpy.PGPKey.from_blob(recipient_public_key)
    
    # Load the sender's private key
    priv_key, _ = pgpy.PGPKey.from_blob(sender_private_key)
    
    # Unlock the sender's private key with the passphrase
    with priv_key.unlock(passphrase):
        # Create a PGPMessage object from the plaintext message
        pgp_message = pgpy.PGPMessage.new(message)
        
        # Sign the message
        signed_message = priv_key.sign(pgp_message)
        
        # Encrypt the signed message with the recipient's public key
        encrypted_message = pub_key.encrypt(signed_message)
    
    return str(encrypted_message)


def generate_salt():
    return os.urandom(16)


def hash_password(password):
    secret_key = settings.SECRET_KEY.encode('utf-8')
    salt = generate_salt()
    # Create HMAC obj
    hmac_obj = hmac.new(secret_key, salt + password.encode('utf-8'), hashlib.sha256)
    # Compute HMAC
    hashed_password = salt + hmac_obj.digest()
    return hashed_password


def check_password(password, hashed_password):
    secret_key = settings.SECRET_KEY.encode('utf-8')
    salt = hashed_password[:16]
    stored_hash = bytes.fromhex(hashed_password[16:])
    # Create HMAC obj with password and salt
    hmac_obj = hmac.new(secret_key, salt.encode('utf-8') + password.encode('utf-8'), hashlib.sha256)
    # Compute HMAC
    new_hash = hmac_obj.digest()
    # Compare computed HMAC and stored hash
    return hmac.compare_digest(stored_hash, new_hash)