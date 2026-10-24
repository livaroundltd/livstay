"""LivStay Level 0 and Level 1 conformance checks against a live Host Platform (spec §16).

  python3 tools/conformance.py https://stay.example
  python3 tools/conformance.py http://localhost:8765      # plain http is allowed only for localhost

Makes only public requests and creates at most two Quotes. Exit code 0 when every check passes.
Needs: pip install jsonschema cryptography
"""
import datetime as dt, json, os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import schema_errors
from livstay_jws import verify_quote, canonical, VerifyError
from reconcile import quote_problems

EXT, REV = "livstay.org/stays", "0.2"
results = []


def http(method, url, body=None, rev=REV):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    if rev:
        req.add_header("LivStay-Revision", rev)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, dict(e.headers), json.loads(raw or b"null")
        except ValueError:
            return e.code, dict(e.headers), None


def check(cid, title, ok, detail=""):
    results.append((cid, title, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {title}" + (f"  — {detail}" if detail and not ok else ""))
    return ok


def schema(cid, title, defname, obj):
    errs = schema_errors(defname, obj)
    return check(cid, title, not errs, "; ".join(errs[:3]))


def main(origin):
    origin = origin.rstrip("/")
    local = origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
    if not (origin.startswith("https://") or local):
        sys.exit("Use https:// (plain http only for localhost).")

    s, h, pj = http("GET", origin + "/.well-known/poppy.json", rev=None)
    if not check("L0.1", "poppy.json is served as JSON", s == 200 and isinstance(pj, dict), f"status {s}"):
        return
    check("L0.2", "poppy.json protocol_version is 0.2", pj.get("protocol_version") == "0.2", str(pj.get("protocol_version")))
    ext = (pj.get("extensions") or {}).get(EXT)
    if not check("L0.3", f"extensions lists {EXT}", isinstance(ext, dict)):
        return
    if not schema("L0.4", "extension entry matches ExtensionEntry", "ExtensionEntry", ext):
        return
    revs = ext.get("revisions_supported", [ext["revision"]])
    if not check("L0.5", f"serves revision {REV}", REV in revs, f"serves {revs}"):
        return
    ep = ext["endpoint"].rstrip("/")
    check("L0.6", "endpoint is HTTPS", ep.startswith("https://") or local, ep)

    s, h, page = http("GET", ep + "/homes")
    if not check("L0.7", "GET /homes works with no token", s == 200, f"status {s}"):
        return
    check("L0.8", "LivStay-Revision is echoed", h.get("LivStay-Revision") == REV, str(h.get("LivStay-Revision")))
    if not schema("L0.9", "homes page matches HomesPage", "HomesPage", page) or not page["homes"]:
        check("L0.10", "at least one Home is published", bool(page and page.get("homes")))
        return
    homes = page["homes"][:3]
    for i, hm in enumerate(homes):
        s, _, one = http("GET", f"{ep}/homes/{hm['home_id']}")
        schema(f"L0.11.{i}", f"GET /homes/{hm['home_id']} matches Home", "Home", one if s == 200 else {})
        if s == 200:
            check(f"L0.12.{i}", "Facts cancellation sentence is present", bool(one["facts"]["cancellation"].strip()))
    s, _, err = http("GET", ep + "/homes", rev="9.9")
    check("L0.13", "unknown revision is refused with revision_unsupported",
          s == 400 and isinstance(err, dict) and err.get("error") == "revision_unsupported" and REV in err.get("supported", []),
          f"status {s}, body {err}")

    if ext["level"] < 1:
        return
    s, _, jwks = http("GET", ext["keys"], rev=None)
    ok = s == 200 and isinstance(jwks, dict) and jwks.get("keys")
    check("L1.1", "keys is a JWK Set", ok, f"status {s}")
    if ok:
        check("L1.2", "every key has kid, use=sig and alg",
              all(k.get("kid") and k.get("use") == "sig" and k.get("alg") in ("ES256", "EdDSA") for k in jwks["keys"]))
    home = homes[0]
    start = dt.date.today() + dt.timedelta(days=1)
    s, _, av = http("GET", f"{ep}/homes/{home['home_id']}/availability?from={start}&to={start + dt.timedelta(days=90)}")
    if not schema("L1.3", "availability matches Availability", "Availability", av if s == 200 else {}):
        return
    days, stay = av["days"], None
    for i, d in enumerate(days):
        n = max(d["min_nights"], home["terms"]["min_nights"])
        run = days[i:i + n]
        if len(run) == n and all(x["available"] for x in run) and not d["closed_to_arrival"]:
            stay = (d["date"], str(dt.date.fromisoformat(d["date"]) + dt.timedelta(days=n)))
            break
    if not check("L1.4", "an available stay exists in the next 90 days", stay):
        return
    body = {"check_in": stay[0], "check_out": stay[1], "party": {"adults": 2, "children": [], "pets": 0}}
    s, h, q = http("POST", f"{ep}/homes/{home['home_id']}/quotes", body)
    if not check("L1.5", "POST quotes works with no token and returns 201", s == 201, f"status {s}, body {q}"):
        return
    if not schema("L1.6", "Quote matches Quote", "Quote", q):
        return
    check("L1.7", "Quote echoes the Stay asked for",
          q["check_in"] == stay[0] and q["check_out"] == stay[1] and q["party"] == body["party"] and q["home_id"] == home["home_id"])
    try:
        verify_quote(q, jwks); sig = ""
    except VerifyError as e:
        sig = str(e)
    check("L1.8", "Quote signature verifies against keys (§13.2)", not sig, sig)
    probs = quote_problems(q)
    check("L1.9", "Quote reconciles (§2.1)", not probs, "; ".join(probs[:3]))
    c, e = (dt.datetime.fromisoformat(q[k].replace("Z", "+00:00")) for k in ("created_at", "expires_at"))
    check("L1.10", "Quote expires within 24 hours", dt.timedelta(0) < e - c <= dt.timedelta(hours=24), f"{e - c}")
    s, _, again = http("GET", f"{ep}/quotes/{q['quote_id']}")
    check("L1.11", "GET /quotes/{id} returns the same Quote", s == 200 and canonical(again) == canonical(q), f"status {s}")
    big = dict(body, party={"adults": home["terms"]["max_guests"] + 1, "children": [], "pets": 0})
    s, _, err = http("POST", f"{ep}/homes/{home['home_id']}/quotes", big)
    check("L1.12", "a Party over max_guests is refused with stay_invalid",
          s == 400 and isinstance(err, dict) and err.get("error") == "stay_invalid", f"status {s}, body {err}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)
