import pgpy


def encrypt_message(message, public_key):
    try:
        # Load public key
        public_key, _ = pgpy.PGPKey.from_blob(public_key)
        
        # Create PGP message
        pgp_message = pgpy.PGPMessage.new(message)
        
        # Encrypt message
        encrypted_message = public_key.encrypt(pgp_message)
        
        return str(encrypted_message)
    
    except ValueError as ve:
        return {"error": str(ve)}


def decrypt_message(encrypted_message, private_key, passphrase):
    try:
        # Load private key
        private_key, _ = pgpy.PGPKey.from_blob(private_key)
        
        # Unlock private key with passphrase
        with private_key.unlock(passphrase):
            # Load encrypted message
            enc_msg = pgpy.PGPMessage.from_blob(encrypted_message)
            decrypt_msg = private_key.decrypt(enc_msg)
            
        return {"message": str(decrypt_msg.message)}
    
    except ValueError as ve:
        return {"error": str(ve)}


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


def verify_message(signed_message, sender_public_key):
    # Load the sender's public key
    pub_key, _ = pgpy.PGPKey.from_blob(sender_public_key)
    
    # Load the signed message
    signed_pgp_message = pgpy.PGPMessage.from_blob(signed_message)
    
    # Verify the signature
    verification = pub_key.verify(signed_pgp_message)
    
    if verification:
        print("Signature is valid.")
        return signed_pgp_message.message
    else:
        print("Signature verification failed.")
        return {"error": "Signature verification failed."}


def encrypt_and_sign_message(message, recipient_public_key, sender_private_key, passphrase):
    try:
        # Load the recipient's public key
        pub_key, _ = pgpy.PGPKey.from_blob(recipient_public_key)
        
        # Check if the public key has the encryption flag
        if not any(uid.selfsig.key_flags & {pgpy.constants.KeyFlags.EncryptCommunications, pgpy.constants.KeyFlags.EncryptStorage} for uid in pub_key.userids):
            raise ValueError("Recipient's public key is not valid for encryption.")
        
        # Load the sender's private key
        priv_key, _ = pgpy.PGPKey.from_blob(sender_private_key)
        
        # Unlock the sender's private key with the passphrase
        with priv_key.unlock(passphrase):
            # Create a PGPMessage object from the plaintext message
            msg = pgpy.PGPMessage.new(message)
            
            # Sign the message using the sender's private key
            msg |= priv_key.sign(msg)
            
            # Encrypt the signed message with the recipient's public key
            encrypted_message = pub_key.encrypt(msg)
        
        return str(encrypted_message)
    
    except ValueError as ve:
        return {"error": str(ve)}


def decrypt_and_verify_message(encrypted_message, recipient_private_key, passphrase, sender_public_key):
    try:
        # Load the recipient's private key
        priv_key, _ = pgpy.PGPKey.from_blob(recipient_private_key)
        
        # Unlock the recipient's private key with the passphrase
        with priv_key.unlock(passphrase):
            # Decrypt the message
            decrypted_message = priv_key.decrypt(pgpy.PGPMessage.from_blob(encrypted_message))
            
        # Load the sender's public key
        pub_key, _ = pgpy.PGPKey.from_blob(sender_public_key)
        
        # Verify the signature
        if pub_key.verify(decrypted_message):
            print("Signature is valid.")
            return {"message": str(decrypted_message.message)}
        else:
            print("Signature verification failed.")
            return {"error": "Signature verification failed."}
        
    except ValueError as ve:
        return {"error": str(ve)}