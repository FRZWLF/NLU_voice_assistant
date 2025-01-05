from threading import Lock, Timer
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from flask import jsonify
from loguru import logger

# Schlüssel-Speicher
KEY_STORAGE = {}
KEY_STORAGE_LOCK = Lock()

# RSA-Schlüsselpaar
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

def store_key(key_id, key, ttl=60):
    with KEY_STORAGE_LOCK:
        KEY_STORAGE[key_id] = key
    Timer(ttl, lambda: remove_key(key_id)).start()

def remove_key(key_id):
    with KEY_STORAGE_LOCK:
        KEY_STORAGE.pop(key_id, None)

def exchange_key_with_client(aes_key):
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key

def decrypt_aes_key(encrypted_key):
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return aes_key

def get_public_key():
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    logger.info(f"Public Key (PEM-Format): {public_key_pem.decode('utf-8')}")
    return jsonify({"public_key": public_key_pem.decode('utf-8')})