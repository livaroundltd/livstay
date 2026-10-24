"""A minimal Level 1 Host Platform for trying tools/conformance.py and agent code locally.

  python3 tools/mock_host.py 8765     # then: python3 tools/conformance.py http://localhost:8765

Serves one Home from the fixtures and signs Quotes with the published TEST key. Not for production.
"""
import json, os, sys, uuid, datetime as dt
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from livstay_jws import sign

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "fixtures", "0.2")
PRIV = json.load(open(os.path.join(F, "TEST-ONLY-signing-key.jwk.json")))
KEYS = json.load(open(os.path.join(F, "keys.json")))
HOME = json.load(open(os.path.join(F, "valid", "home.json")))
REV, QUOTES = "0.2", {}
NIGHTLY, CLEANING = Decimal("18000.00"), Decimal("3500.00")


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def money(d):
    return {"amount": f"{d.quantize(Decimal('0.01'))}", "currency": "INR"}


class H(BaseHTTPRequestHandler):
    def base(self):
        return f"http://{self.headers['Host']}"

    def send(self, code, body, rev=True):
        b = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        if rev:
            self.send_header("LivStay-Revision", REV)
        self.end_headers()
        self.wfile.write(b)

    def rev_ok(self):
        r = self.headers.get("LivStay-Revision")
        if r and r != REV:
            self.send(400, {"error": "revision_unsupported", "supported": [REV]})
            return False
        return True

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/.well-known/poppy.json":
            return self.send(200, {"protocol_version": "0.2", "organization": {"name": "Mock Stays", "domain": self.headers["Host"]},
                "apis": [{"type": "openapi", "url": f"{self.base()}/livstay/v0/openapi.json"}],
                "extensions": {"livstay.org/stays": {"version": "0", "revision": REV, "endpoint": f"{self.base()}/livstay/v0",
                                                     "level": 1, "keys": f"{self.base()}/.well-known/livstay-keys.json"}}}, rev=False)
        if p == "/.well-known/livstay-keys.json":
            return self.send(200, KEYS, rev=False)
        if not self.rev_ok():
            return
        if p == "/livstay/v0/homes":
            return self.send(200, {"homes": [HOME], "next_cursor": None})
        if p == f"/livstay/v0/homes/{HOME['home_id']}":
            return self.send(200, HOME)
        if p == f"/livstay/v0/homes/{HOME['home_id']}/availability":
            start = (now() + dt.timedelta(days=30)).date()
            days = [{"date": str(start + dt.timedelta(days=i)), "available": True, "min_nights": 3,
                     "closed_to_arrival": False, "closed_to_departure": False, "nightly": money(NIGHTLY)} for i in range(30)]
            return self.send(200, {"home_id": HOME["home_id"], "time_zone": HOME["time_zone"], "currency": "INR",
                                   "days": days, "generated_at": ts(now()), "ttl_seconds": 300})
        if p.startswith("/livstay/v0/quotes/") and p.split("/")[-1] in QUOTES:
            return self.send(200, QUOTES[p.split("/")[-1]])
        if p == "/livstay/v0/tier-issuers":
            return self.send(200, {"issuers": []})
        self.send(404, {"error": "not_found"})

    def do_POST(self):
        p = self.path.split("?")[0]
        if not self.rev_ok():
            return
        if p != f"/livstay/v0/homes/{HOME['home_id']}/quotes":
            return self.send(404, {"error": "not_found"})
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        party = req["party"]
        ci, co = dt.date.fromisoformat(req["check_in"]), dt.date.fromisoformat(req["check_out"])
        n = (co - ci).days
        t = HOME["terms"]
        guests = party["adults"] + sum(1 for c in party["children"] if c["age"] >= t["infant_max_age"])
        if n < t["min_nights"] or n > t["max_nights"]:
            return self.send(400, {"error": "stay_invalid", "rule": "min_nights" if n < t["min_nights"] else "max_nights"})
        if guests > t["max_guests"]:
            return self.send(400, {"error": "stay_invalid", "rule": "max_guests"})
        nights = NIGHTLY * n
        disc = -(nights * Decimal("0.10")).quantize(Decimal("0.01")) if n >= 7 else Decimal("0.00")
        sub = nights + disc + CLEANING
        tax = (sub * Decimal("0.12")).quantize(Decimal("0.01"))
        total = sub + tax
        lines = [{"kind": "nights", "label": f"{n} nights", "amount": money(nights), "in_total": True},
                 {"kind": "cleaning", "label": "Cleaning", "amount": money(CLEANING), "in_total": True},
                 {"kind": "tax", "label": "GST 12%", "amount": money(tax), "in_total": True}]
        if disc:
            lines.insert(1, {"kind": "discount", "label": "Weekly stay", "amount": money(disc), "in_total": True})
        first = (total * Decimal("0.30")).quantize(Decimal("0.01"))
        ci_at = dt.datetime.combine(ci, dt.time(8, 30), dt.timezone.utc)
        c = now()
        q = {"quote_id": "qt_" + uuid.uuid4().hex[:10], "home_id": HOME["home_id"], "check_in": req["check_in"],
             "check_out": req["check_out"], "party": party, "time_zone": HOME["time_zone"], "terms_version": t["terms_version"],
             "currency": "INR", "lines": lines, "total": money(total),
             "payment_schedule": [{"due_at": None, "at_booking": True, "amount": money(first)},
                                  {"due_at": ts(ci_at - dt.timedelta(days=14)), "at_booking": False, "amount": money(total - first)}],
             "cancellation": [{"until": ts(ci_at - dt.timedelta(days=14)), "refund": money(total)},
                              {"until": ts(ci_at - dt.timedelta(days=7)), "refund": money((total / 2).quantize(Decimal("0.01")))},
                              {"until": None, "refund": money(Decimal(0))}],
             "deposit": {"amount": money(Decimal("15000")), "mode": "authorise"}, "assumed_tier": "new",
             "instant": False, "created_at": ts(c), "expires_at": ts(c + dt.timedelta(hours=24))}
        q["signature"] = sign(q, PRIV, "livstay-quote+jws")
        QUOTES[q["quote_id"]] = q
        self.send(201, q)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Mock LivStay Host Platform on http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
