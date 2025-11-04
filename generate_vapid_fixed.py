from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Δημιουργία ιδιωτικού κλειδιού
private_key = ec.generate_private_key(ec.SECP256R1())

# Δημιουργία δημόσιου κλειδιού
public_key = private_key.public_key()

# Μετατροπή σε base64 (όπως απαιτεί το WebPush)
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")

public_key_b64 = urlsafe_b64encode(public_bytes).decode("utf-8").rstrip("=")
private_key_b64 = urlsafe_b64encode(private_bytes).decode("utf-8").rstrip("=")

print("VAPID_PUBLIC_KEY =", public_key_b64)
print("VAPID_PRIVATE_KEY =", private_key_b64)
