import pgpy


"""
Fungsi ini mengenkripsi pesan plaintext menggunakan public key yang diberikan.
Jika berhasil, fungsi mengembalikan pesan terenkripsi dalam bentuk string.
Jika terjadi kesalahan, fungsi mengembalikan objek JSON dengan pesan error.
"""
def encrypt_message(message, public_key):
    try:
        # Memuat public key
        public_key, _ = pgpy.PGPKey.from_blob(public_key)
        
        # Membuat objek PGPMessage dari pesan
        pgp_message = pgpy.PGPMessage.new(message)
        
        # Mengenkripsi pesan
        encrypted_message = public_key.encrypt(pgp_message)
        
        return str(encrypted_message)
    
    except ValueError as ve:
        return {"error": str(ve)}


"""
Fungsi ini mendekripsi pesan yang telah dienkripsi menggunakan private key yang diberikan 
dan passphrase untuk membuka private key.
Jika berhasil, fungsi mengembalikan objek JSON dengan pesan terdekripsi.
Jika terjadi kesalahan, fungsi mengembalikan objek JSON dengan pesan error.
"""
def decrypt_message(encrypted_message, private_key, passphrase):
    try:
        # Memuat private key
        private_key, _ = pgpy.PGPKey.from_blob(private_key)
        
        # Membuka kunci private key dengan passphrase
        with private_key.unlock(passphrase):
            # Memuat pesan terenkripsi
            enc_msg = pgpy.PGPMessage.from_blob(encrypted_message)
            decrypt_msg = private_key.decrypt(enc_msg)
            
        return {"message": str(decrypt_msg.message)}
    
    except ValueError as ve:
        return {"error": str(ve)}


"""
Fungsi ini menandatangani pesan plaintext menggunakan private key yang diberikan 
dan passphrase untuk membuka private key.
Fungsi mengembalikan pesan yang telah ditandatangani dalam bentuk string.
"""
def sign_message(message, private_key, passphrase):
    # Memuat private key
    priv_key, _ = pgpy.PGPKey.from_blob(private_key)
    
    # Membuka kunci private key dengan passphrase
    with priv_key.unlock(passphrase):
        # Create a PGPMessage object from the plaintext message
        msg = pgpy.PGPMessage.new(message)
        
        # Sign pesan menggunakan private key
        msg |= priv_key.sign(msg)
    
    return str(msg)


"""
Fungsi ini memverifikasi pesan yang telah ditandatangani menggunakan public key pengirim yang diberikan.
Jika tanda tangan valid, fungsi mengembalikan pesan dalam bentuk string.
Jika verifikasi gagal, fungsi mengembalikan objek JSON dengan pesan error.
"""
def verify_message(signed_message, sender_public_key):
    # Memuat public key pengirim
    pub_key, _ = pgpy.PGPKey.from_blob(sender_public_key)
    
    # Memuat pesan
    signed_pgp_message = pgpy.PGPMessage.from_blob(signed_message)
    
    # Memverifikasi signature pesan
    verification = pub_key.verify(signed_pgp_message)
    
    if verification:
        print("Signature is valid.")
        return signed_pgp_message.message
    else:
        print("Signature verification failed.")
        return {"error": "Signature verification failed."}


"""
Fungsi ini mengenkripsi pesan plaintext menggunakan public key penerima yang diberikan,
dan menandatangani pesan tersebut menggunakan private key pengirim dengan passphrase.
Jika berhasil, fungsi mengembalikan pesan terenkripsi dalam bentuk string.
Jika terjadi kesalahan, fungsi mengembalikan objek JSON dengan pesan error.
"""
def encrypt_and_sign_message(message, recipient_public_key, sender_private_key, passphrase):
    try:
        # Memuat public key penerima
        pub_key, _ = pgpy.PGPKey.from_blob(recipient_public_key)
        
        # Memeriksa apakah public key memiliki flag enkripsi
        if not any(uid.selfsig.key_flags & {pgpy.constants.KeyFlags.EncryptCommunications, pgpy.constants.KeyFlags.EncryptStorage} for uid in pub_key.userids):
            raise ValueError("public key penerima tidak valid untuk enkripsi.")
        
        # Memuat private key pengirim
        priv_key, _ = pgpy.PGPKey.from_blob(sender_private_key)
        
        # Membuka private key pengirim dengan passphrase
        with priv_key.unlock(passphrase):
            # Membuat objek PGPMessage dari pesan plaintext
            msg = pgpy.PGPMessage.new(message)
            
            # Menandatangani pesan menggunakan private key pengirim
            msg |= priv_key.sign(msg)
            
            # Mengenkripsi pesan yang ditandatangani dengan public key penerima
            encrypted_message = pub_key.encrypt(msg)
        
        return str(encrypted_message)
    
    except ValueError as ve:
        return {"error": str(ve)}


"""
Fungsi ini mendekripsi pesan yang dienkripsi menggunakan private key penerima,
dan memverifikasi tanda tangan pesan tersebut menggunakan public key pengirim.
Jika berhasil, fungsi mengembalikan pesan terenkripsi dalam bentuk json.
Jika terjadi kesalahan, fungsi mengembalikan objek JSON dengan pesan error.
"""
def decrypt_and_verify_message(encrypted_message, recipient_private_key, passphrase, sender_public_key):
    try:
        # Memuat private key penerima
        priv_key, _ = pgpy.PGPKey.from_blob(recipient_private_key)
        
        # Membuka private keye key penerima dengan passphrase
        with priv_key.unlock(passphrase):
            # Decrypt the message
            decrypted_message = priv_key.decrypt(pgpy.PGPMessage.from_blob(encrypted_message))
            
        # Memuat public key pengirim
        pub_key, _ = pgpy.PGPKey.from_blob(sender_public_key)
        
        # Memverifikasi signature
        if pub_key.verify(decrypted_message):
            print("Signature is valid.")
            return {"message": str(decrypted_message.message)}
        else:
            print("Signature verification failed.")
            return {"error": "Signature verification failed."}
        
    except ValueError as ve:
        return {"error": str(ve)}