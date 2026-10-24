"""Validate LivStay objects (spec §16).

  python3 tools/validate.py                         # check every fixture behaves as its manifest says
  python3 tools/validate.py Quote my-quote.json --keys keys.json   # check one object of your own

Needs: pip install jsonschema cryptography
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonschema import Draft202012Validator, FormatChecker
from livstay_jws import verify, verify_quote, VerifyError
from reconcile import quote_problems, booking_terms_problems

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = json.load(open(os.path.join(ROOT, "schemas", "livstay-0.2.schema.json")))


def validator(defname):
    s = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{defname}"}
    return Draft202012Validator(s, format_checker=FormatChecker())


def schema_errors(defname, obj):
    return [f"{'/'.join(map(str, e.absolute_path)) or '$'}: {e.message}" for e in validator(defname).iter_errors(obj)]


def check(defname, obj, jwks=None, quote=None, typ=None):
    """Returns (stage, problems): stage is where it first failed, or 'valid'."""
    p = schema_errors(defname, obj)
    if p:
        return "schema", p
    if defname == "Quote":
        if jwks is not None:
            try:
                verify_quote(obj, jwks)
            except VerifyError as e:
                return "signature", [str(e)]
        p = quote_problems(obj)
        if p:
            return "reconcile", p
    if defname == "BookingOperation" and quote is not None:
        p = booking_terms_problems(obj["terms"]["livstay"], quote)
        if p:
            return "quote_binding", p
    return "valid", []


def run_fixtures():
    F = os.path.join(ROOT, "fixtures", "0.2")
    man = json.load(open(os.path.join(F, "manifest.json")))
    jwks = json.load(open(os.path.join(F, man["keys"])))
    quote = json.load(open(os.path.join(F, man["quote"])))
    failures = 0
    for fx in man["fixtures"]:
        obj = json.load(open(os.path.join(F, fx["file"])))
        if fx.get("jws_map_typ"):
            stage, probs = "valid", []
            for name, jws in obj.items():
                try:
                    payload = verify(jws, jwks, fx["jws_map_typ"])
                except VerifyError as e:
                    stage, probs = "signature", [f"{name}: {e}"]; break
                errs = schema_errors("ReceiptClaims", payload)
                if errs:
                    stage, probs = "schema", [f"{name}: {x}" for x in errs]; break
        else:
            stage, probs = check(fx["def"], obj, jwks, quote)
        ok = stage == fx["expect"]
        failures += not ok
        mark = "ok  " if ok else "FAIL"
        detail = "" if stage == "valid" else f" ({stage}: {probs[0]})"
        print(f"{mark} {fx['file']}: expected {fx['expect']}, got {stage}{detail}")
    print(f"\n{len(man['fixtures']) - failures}/{len(man['fixtures'])} fixtures behave as expected")
    return failures == 0


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        defname, path = sys.argv[1], sys.argv[2]
        jwks = json.load(open(sys.argv[sys.argv.index("--keys") + 1])) if "--keys" in sys.argv else None
        stage, probs = check(defname, json.load(open(path)), jwks)
        print(stage); [print(" -", p) for p in probs]
        sys.exit(stage != "valid")
    sys.exit(0 if run_fixtures() else 1)
