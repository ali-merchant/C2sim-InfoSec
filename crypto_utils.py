#importing libraries
import hashlib
import json
import os
from typing import Any, Dict
#kci bi
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key(shared_secret: bytes) -> bytes:
    return hashlib.sha256(shared_secret).digest()


def encrypt_payload(key: bytes, payload: Dict[str, Any]) -> Dict[str, str]:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    data = json.dumps(payload).encode("utf-8")
    ct = aesgcm.encrypt(nonce, data, None)
    return {"nonce": nonce.hex(), "ct": ct.hex()}


def decrypt_payload(key: bytes, packet: Dict[str, str]) -> Dict[str, Any]:
    nonce_hex = packet.get("nonce")
    ct_hex = packet.get("ct")
    if not nonce_hex or not ct_hex:
        raise ValueError("packet missing nonce or ct")

    nonce = bytes.fromhex(nonce_hex)
    ct = bytes.fromhex(ct_hex)
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, ct, None)
    return json.loads(data.decode("utf-8"))
