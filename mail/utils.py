import gnupg

gpg = gnupg.GPG()

def encrypt_message(message, public_key):
    import_result = gpg.import_keys(public_key)
    if not import_result:
        raise ValueError('Failed to import public key.')

    # Encrypt message
    encrypted_message = gpg.encrypt(message, import_result.fingerprints)
    if not encrypted_message.ok:
        raise ValueError('Failed to encrypt message: ' + str(encrypted_message.status))
    
    return str(encrypted_message)


def decrypt_message(encrypted_message, private_key, passphrase):
    import_result = gpg.import_keys(private_key)
    if not import_result:
        raise ValueError('Failed to import private key.')

    # Decrypt message
    decrypted_message = gpg.decrypt(encrypted_message, passphrase=passphrase)
    if not decrypted_message.ok:
        raise ValueError('Failed to decrypt message: ' + str(decrypted_message.status))
    
    return str(decrypted_message)