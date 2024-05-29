import hmac
import hashlib

# Returns the HMAC of a message
def generate_hmac(message, secret_key):
    calc_hmac = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calc_hmac


# Return True if the HMAC of the message is equal to the received HMAC
def verify_hmac(message, secret_key, received_hmac):
    calc_hmac = generate_hmac(message, secret_key)
    return hmac.compare_digest(calc_hmac, received_hmac)