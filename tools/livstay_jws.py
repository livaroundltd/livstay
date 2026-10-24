"""Canonical JSON, signing and verification for LivStay signed objects (spec §13.1–§13.2).

Needs: pip install cryptography
"""
import base64, hashlib, json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, utils
from cryptography.exceptions import InvalidSignature

TYPS = {"livstay-quote+jws", "livstay-receipt+jws", "livstay-answer+jws"}
ALLOWED_ALGS = {"ES256", "EdDSA"}


class VerifyError(Exception):
    pass


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def b64u_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _check_no_fractions(v, path="$"):
    if isinstance(v, float):
        raise ValueError(f"{path}: signed objects must not contain fractional numbers (spec §2.1)")
    if isinstance(v, dict):
        for k, x in v.items():
            _check_no_fractions(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _check_no_fractions(x, f"{path}[{i}]")


def canonical(obj) -> bytes:
    """RFC 8785 for objects without fractional numbers: sorted keys (UTF-16 order), no whitespace."""
    _check_no_fractions(obj)

    def enc(v):
        if isinstance(v, dict):
            items = sorted(v.items(), key=lambda kv: kv[0].encode("utf-16-be"))
            return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + enc(x) for k, x in items) + "}"
        if isinstance(v, list):
            return "[" + ",".join(enc(x) for x in v) + "]"
        return json.dumps(v, ensure_ascii=False)

    return enc(obj).encode("utf-8")


def terms_hash(terms_livstay) -> str:
    return b64u(hashlib.sha256(canonical(terms_livstay)).digest())


def _public_key(jwk):
    if jwk.get("kty") == "EC" and jwk.get("crv") == "P-256":
        x = int.from_bytes(b64u_dec(jwk["x"]), "big")
        y = int.from_bytes(b64u_dec(jwk["y"]), "big")
        return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
    if jwk.get("kty") == "OKP" and jwk.get("crv") == "Ed25519":
        return ed25519.Ed25519PublicKey.from_public_bytes(b64u_dec(jwk["x"]))
    raise VerifyError(f"unsupported key type for kid {jwk.get('kid')}")


def sign(obj, private_jwk, typ) -> str:
    """Sign obj with an ES256 private JWK (with 'd'). For tests and reference implementations."""
    assert typ in TYPS
    header = {"alg": "ES256", "kid": private_jwk["kid"], "typ": typ}
    d = int.from_bytes(b64u_dec(private_jwk["d"]), "big")
    key = ec.derive_private_key(d, ec.SECP256R1())
    signing_input = (b64u(canonical(header)) + "." + b64u(canonical(obj))).encode()
    der = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der)
    return signing_input.decode() + "." + b64u(r.to_bytes(32, "big") + s.to_bytes(32, "big"))


def verify(jws: str, jwks: dict, expected_typ: str) -> dict:
    """Spec §13.2 steps 1, 3, 4 and the decode in 5. Returns the payload object."""
    try:
        h64, p64, s64 = jws.split(".")
        header = json.loads(b64u_dec(h64))
    except Exception as e:
        raise VerifyError(f"not a compact JWS: {e}")
    alg, kid, typ = header.get("alg"), header.get("kid"), header.get("typ")
    if alg not in ALLOWED_ALGS:
        raise VerifyError(f"alg {alg!r} not allowed")
    if typ != expected_typ:
        raise VerifyError(f"typ {typ!r}, expected {expected_typ!r}")
    if not kid:
        raise VerifyError("missing kid")
    jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk is None:
        raise VerifyError(f"unknown kid {kid!r} (refetch keys once before giving up)")
    if jwk.get("alg") and jwk["alg"] != alg:
        raise VerifyError(f"key alg {jwk['alg']} does not match header alg {alg}")
    sig = b64u_dec(s64)
    data = (h64 + "." + p64).encode()
    pub = _public_key(jwk)
    try:
        if alg == "ES256":
            if len(sig) != 64:
                raise VerifyError("ES256 signature must be 64 bytes")
            der = utils.encode_dss_signature(int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big"))
            pub.verify(der, data, ec.ECDSA(hashes.SHA256()))
        else:
            pub.verify(sig, data)
    except InvalidSignature:
        raise VerifyError("bad signature")
    return json.loads(b64u_dec(p64))


def verify_quote(quote: dict, jwks: dict) -> dict:
    """Spec §13.2 step 5 for Quotes: the payload must equal the received Quote without signature."""
    payload = verify(quote["signature"], jwks, "livstay-quote+jws")
    body = {k: v for k, v in quote.items() if k != "signature"}
    if canonical(payload) != canonical(body):
        raise VerifyError("Quote fields differ from the signed payload")
    return payload
