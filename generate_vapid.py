from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Δημιουργία νέου ECDSA κλειδιού για VAPID
private_key = ec.generate_private_key(ec.SECP256R1())

# Απόκτηση public key
public_key = (
    private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
)

# Μετατροπή σε Base64 (URL-safe)
def to_b64url(b):
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

vapid_private_key = to_b64url(
    private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
)

vapid_public_key = to_b64url(public_key)

print("VAPID_PUBLIC_KEY =", vapid_public_key)
print("VAPID_PRIVATE_KEY =", vapid_private_key)
