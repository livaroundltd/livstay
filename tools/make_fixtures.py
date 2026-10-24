"""Regenerates fixtures/0.2/. Signatures change on every run (ECDSA), so only rerun when fixtures change.

Usage: python3 tools/make_fixtures.py [--new-key]
"""
import copy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from livstay_jws import sign, terms_hash, b64u
from cryptography.hazmat.primitives.asymmetric import ec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "fixtures", "0.2")
os.makedirs(os.path.join(F, "valid"), exist_ok=True)
os.makedirs(os.path.join(F, "invalid"), exist_ok=True)
KEYF = os.path.join(F, "TEST-ONLY-signing-key.jwk.json")

if "--new-key" in sys.argv or not os.path.exists(KEYF):
    k = ec.generate_private_key(ec.SECP256R1())
    n = k.private_numbers()
    priv = {"kty": "EC", "crv": "P-256", "kid": "test-2026-10", "use": "sig", "alg": "ES256",
            "x": b64u(n.public_numbers.x.to_bytes(32, "big")), "y": b64u(n.public_numbers.y.to_bytes(32, "big")),
            "d": b64u(n.private_value.to_bytes(32, "big")),
            "_warning": "TEST KEY. Published on purpose so anyone can reproduce the fixtures. Never use it to sign anything real."}
    json.dump(priv, open(KEYF, "w"), indent=2)
priv = json.load(open(KEYF))
pub = {k: v for k, v in priv.items() if k not in ("d", "_warning")}
json.dump({"keys": [pub]}, open(os.path.join(F, "keys.json"), "w"), indent=2)

M = lambda a: {"amount": a, "currency": "INR"}
PARTY = {"adults": 4, "children": [{"age": 7}, {"age": 1}], "pets": 0}
ISS = "https://stay.example"
manifest = []


def put(kind, name, obj, d, expect="valid", typ=None):
    path = f"{kind}/{name}.json"
    json.dump(obj, open(os.path.join(F, path), "w"), indent=2, ensure_ascii=False)
    e = {"file": path, "def": d, "expect": expect}
    if typ:
        e["jws_typ"] = typ
    manifest.append(e)


ext = {"version": "0", "revision": "0.2", "endpoint": f"{ISS}/livstay/v0", "level": 3,
       "keys": f"{ISS}/.well-known/livstay-keys.json", "terms_of_service": f"{ISS}/terms"}
put("valid", "extension-entry", ext, "ExtensionEntry")
put("valid", "client-extension-entry", {"version": "0", "revisions": ["0.2"]}, "ClientExtensionEntry")

terms = {"terms_version": 12, "decision_mode": "instant", "instant_min_tier": "verified", "id_required": True,
         "min_nights": 3, "max_nights": 28, "max_guests": 6, "infant_max_age": 2, "infants_count": False,
         "max_infants": 1, "pets": {"allowed": False, "max": 0, "note": "No pets: the garden is shared."},
         "discounts": [{"kind": "weekly", "percent": 10}], "channel_adjustment_percent": 0,
         "cancellation": [{"until_days_before": 14, "refund_percent": 100}, {"until_days_before": 7, "refund_percent": 50},
                          {"until_days_before": 0, "refund_percent": 0}],
         "deposit": {"amount": M("15000.00"), "mode": "authorise"},
         "payment_schedule": [{"due": "at_booking", "percent": 30}, {"due": "days_before_check_in", "days": 14, "percent": 70}],
         "taxes": [{"name": "GST", "percent": 12, "included": False}]}
home = {"home_id": "home_7Qp2", "name": "Casa Mira", "url": "https://stays.example/homes/casa-mira",
        "time_zone": "Asia/Kolkata",
        "description": {"@type": "House", "numberOfBedrooms": 3, "numberOfBathroomsTotal": 3, "occupancy": {"maxValue": 6}},
        "location": {"area": "Assagao, North Goa", "country": "IN", "lat": 15.59, "lng": 73.79, "precision_m": 1000},
        "host": {"display_name": "Rhea", "host_since": 2017, "languages": ["en", "hi", "kok"], "response_time_p50_minutes": 25},
        "facts": {"facts_version": 9, "summary": "A three-bedroom Portuguese-era house with a fenced pool, ten minutes from Assagao's cafes. Suits families and small groups who want quiet.",
                  "ideal_for": ["families with small children", "remote work"], "not_for": ["parties", "guests who need step-free access"],
                  "accessibility": [], "check_in": {"from": "14:00", "until": "22:00", "how": "the host meets you"},
                  "check_out": {"by": "11:00"}, "included": ["daily cleaning", "breakfast"], "not_included": ["airport pickup"],
                  "power_backup": "Full-house inverter, 6 hours.", "internet": "Fibre, 200 Mbps.",
                  "parking": "Two cars in the drive.", "pets": "No pets.", "smoking": "Outdoors only.",
                  "noise": "Quiet after 22:00.", "children": "Cot and high chair on request.",
                  "house_rules": ["No parties", "Quiet after 22:00"],
                  "cancellation": "Full refund until 14 days before check-in, half until 7 days, then none.",
                  "when_things_go_wrong": "Message Rhea through the booking conversation; the caretaker lives next door."},
        "terms": terms,
        "protection": {"underwriter": "host", "evidence": "Photos at check-in and check-out, kept by the caretaker.",
                       "rules_url": "https://stays.example/claims", "claim_response_hours": 72,
                       "appeal": "To the Host Platform within 5 days; decided by someone other than the host."},
        "photos": [{"url": "https://stays.example/p/casa-mira-pool.jpg", "caption": "The fenced pool", "taken_on": "2026-08-02"}],
        "photos_updated_at": "2026-08-02T09:00:00Z", "currency": "INR", "updated_at": "2026-10-20T12:00:00Z"}
put("valid", "home", home, "Home")
put("valid", "homes-page", {"homes": [home], "next_cursor": None}, "HomesPage")
put("valid", "availability", {"home_id": "home_7Qp2", "time_zone": "Asia/Kolkata", "currency": "INR",
    "days": [{"date": "2026-12-27", "available": True, "min_nights": 3, "closed_to_arrival": False,
              "closed_to_departure": False, "nightly": M("18000.00")}],
    "generated_at": "2026-10-24T09:00:00Z", "ttl_seconds": 300}, "Availability")
put("valid", "quote-request", {"check_in": "2026-12-27", "check_out": "2027-01-03", "party": PARTY}, "QuoteRequest")

q = {"quote_id": "qt_P8m1", "home_id": "home_7Qp2", "check_in": "2026-12-27", "check_out": "2027-01-03",
     "party": PARTY, "time_zone": "Asia/Kolkata", "terms_version": 12, "currency": "INR",
     "lines": [{"kind": "nights", "label": "7 nights", "amount": M("126000.00"), "in_total": True},
               {"kind": "discount", "label": "Weekly stay, 10% off nights", "amount": M("-12600.00"), "in_total": True},
               {"kind": "cleaning", "label": "Cleaning", "amount": M("3500.00"), "in_total": True},
               {"kind": "extra_guest", "label": "Child aged 7, 7 nights", "amount": M("2800.00"), "in_total": True},
               {"kind": "tax", "label": "GST", "amount": M("6633.00"), "in_total": True},
               {"kind": "platform_fee", "label": "LivAround fee", "amount": M("3167.00"), "in_total": True}],
     "total": M("129500.00"),
     "payment_schedule": [{"due_at": None, "at_booking": True, "amount": M("38850.00")},
                          {"due_at": "2026-12-13T08:30:00Z", "at_booking": False, "amount": M("90650.00")}],
     "cancellation": [{"until": "2026-12-13T08:30:00Z", "refund": M("129500.00")},
                      {"until": "2026-12-20T08:30:00Z", "refund": M("64750.00")},
                      {"until": None, "refund": M("0.00")}],
     "deposit": {"amount": M("15000.00"), "mode": "authorise"}, "assumed_tier": "trusted", "instant": True,
     "created_at": "2026-10-24T09:00:00Z", "expires_at": "2026-10-25T09:00:00Z"}
quote = dict(q, signature=sign(q, priv, "livstay-quote+jws"))
put("valid", "quote", quote, "Quote", typ="livstay-quote+jws")

put("valid", "booking-request", {"quote_id": "qt_P8m1", "trip_context": {"purpose": "family new year",
    "arrival_notes": "landing 23:40"}}, "BookingRequest")
lt = {"revision": "0.2", "action": "book", "quote_id": "qt_P8m1", "quote_signature": quote["signature"],
      "home_id": "home_7Qp2", "check_in": "2026-12-27", "check_out": "2027-01-03", "party": PARTY,
      "total": M("129500.00"), "due_now": M("38850.00"), "deposit": {"amount": M("15000.00"), "mode": "authorise"},
      "terms_version": 12, "tier": {"presented": True, "accepted": True, "applied": "trusted"},
      "requirements": ["payment", "identity_verification"], "awaiting": "traveller", "proposed_by": "traveller_agent"}
op = {"operation_id": "bk_4Hn9", "revision": 1, "state": "proposed",
      "summary": "Casa Mira, Assagao: 27 Dec 2026 to 3 Jan 2027, 4 adults, a 7-year-old and an infant. Total INR 1,29,500.00 including taxes and fees; INR 38,850.00 now, the rest by 13 Dec. Free cancellation until 13 Dec, half back until 20 Dec, then none. Deposit INR 15,000.00 authorised on your card. You will be asked to verify your identity. Booked with Example Stays for host Rhea.",
      "terms": {"livstay": lt}, "expires_at": "2026-10-24T09:20:00Z", "user_approval_required": True,
      "url": "https://stays.example/b/bk_4Hn9", "confirmation": None, "result": None}
put("valid", "booking-operation-proposed", op, "BookingOperation")
put("valid", "completion", {"operation_id": "bk_4Hn9", "complete_by": "2026-10-24T10:21:00Z",
    "requirements": [{"type": "payment", "status": "pending", "url": "https://stays.example/pay/bk_4Hn9", "amount": M("38850.00")},
                     {"type": "identity_verification", "status": "done", "url": None}]}, "Completion")

rc = {"iss": ISS, "revision": "0.2", "receipt_id": "rcp_9Tq1", "action": "confirm", "initiated_by": "traveller_agent",
      "sub": "usr_83jd", "client_id": "https://agent.example/client.json", "scopes": ["livstay:book", "poppy:read"],
      "operation_id": "bk_4Hn9", "revision_no": 1, "terms_hash": terms_hash(lt), "confirmed": True,
      "approved_by": "user", "iat": 1792760461}
put("valid", "receipt-confirm-claims", rc, "ReceiptClaims")
r_confirm = sign(rc, priv, "livstay-receipt+jws")
rp = {"iss": ISS, "revision": "0.2", "receipt_id": "rcp_9Tq2", "action": "payment_received", "initiated_by": "host_platform",
      "sub": "usr_83jd", "booking_id": "bkg_4Hn9", "event_id": "evt_1", "amount": M("38850.00"),
      "reference": "pay_81kq", "iat": 1792760900}
put("valid", "receipt-payment-claims", rp, "ReceiptClaims")
r_pay = sign(rp, priv, "livstay-receipt+jws")
put("valid", "booking-result", {"revision": "0.2", "booking_id": "bkg_4Hn9", "home_id": "home_7Qp2",
    "check_in": "2026-12-27", "check_out": "2027-01-03", "party": PARTY,
    "location": {"address": "House 14, Mapusa Road, Assagao, Goa 403507", "lat": 15.5931, "lng": 73.7902},
    "check_in_instructions": "Sent on 26 Dec.", "receipt": r_confirm}, "BookingResult")
ev = {"event_id": "evt_1", "booking_id": "bkg_4Hn9", "type": "payment_received", "at": "2026-10-24T09:28:20Z",
      "summary": "INR 38,850.00 received.", "data": {"amount": M("38850.00"), "reference": "pay_81kq"}, "receipt": r_pay}
put("valid", "event-payment-received", ev, "Event")
put("valid", "events-page", {"events": [ev], "cursor": "evt_1", "has_more": False}, "EventsPage")
put("valid", "contact-request", {"share": ["phone"]}, "ContactRequest")
put("valid", "contact-state", {"shared": ["phone"], "host_contact": {"name": "Rhea", "phone": "+910000000000", "email": None},
    "receipt": r_confirm}, "ContactState")
json.dump({"confirm": r_confirm, "payment_received": r_pay}, open(os.path.join(F, "valid", "receipts.jws.json"), "w"), indent=2)
manifest.append({"file": "valid/receipts.jws.json", "def": None, "expect": "valid", "jws_map_typ": "livstay-receipt+jws"})

# invalid
bad = copy.deepcopy(q); bad["lines"][2]["amount"] = M("3600.00"); bad["quote_id"] = "qt_Bad1"
put("invalid", "quote-lines-do-not-sum", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", "reconcile", "livstay-quote+jws")
bad = copy.deepcopy(q); bad["payment_schedule"][0]["amount"] = M("38850.0"); bad["quote_id"] = "qt_Bad2"
put("invalid", "quote-wrong-precision", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", "reconcile", "livstay-quote+jws")
bad = copy.deepcopy(quote); bad["total"] = M("119500.00")
put("invalid", "quote-tampered-after-signing", bad, "Quote", "signature", "livstay-quote+jws")
put("invalid", "receipt-approval-without-confirmation", dict(rc, confirmed=False), "ReceiptClaims", "schema")
put("invalid", "extension-level-1-without-keys", {k: v for k, v in dict(ext, level=1).items() if k not in ("keys",)}, "ExtensionEntry", "schema")
put("invalid", "party-without-adults", {"check_in": "2026-12-27", "check_out": "2027-01-03",
    "party": {"adults": 0, "children": [], "pets": 0}}, "QuoteRequest", "schema")
put("invalid", "money-event-without-receipt", {k: v for k, v in ev.items() if k != "receipt"}, "Event", "schema")
bad = copy.deepcopy(home); del bad["time_zone"]
put("invalid", "home-without-time-zone", bad, "Home", "schema")
bad = copy.deepcopy(q); bad["quote_id"] = "qt_Bad3"
bad["cancellation"][0]["until"], bad["cancellation"][1]["until"] = bad["cancellation"][1]["until"], bad["cancellation"][0]["until"]
put("invalid", "quote-cancellation-out-of-order", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", "reconcile", "livstay-quote+jws")
bad_op = copy.deepcopy(op); bad_op["terms"]["livstay"]["due_now"] = {"amount": "38850.00", "currency": "USD"}
put("invalid", "booking-due-now-wrong-currency", bad_op, "BookingOperation", "quote_binding")
bad = copy.deepcopy(q); bad["quote_id"] = "qt_Bad4"; bad["deposit"]["amount"] = M("-15000.00")
put("invalid", "quote-negative-deposit", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", "reconcile", "livstay-quote+jws")
bad = copy.deepcopy(q); bad["quote_id"] = "qt_Bad5"
bad["payment_schedule"][0]["amount"], bad["payment_schedule"][1]["amount"] = M("-1.00"), M("129501.00")
put("invalid", "quote-negative-instalment", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", "reconcile", "livstay-quote+jws")
bad_op = copy.deepcopy(op); bad_op["terms"]["livstay"]["home_id"] = "home_other"
put("invalid", "booking-other-home", bad_op, "BookingOperation", "quote_binding")
cancel_op = copy.deepcopy(op); cl = cancel_op["terms"]["livstay"]
for k in ("quote_id", "quote_signature", "total", "due_now", "deposit", "tier", "requirements"):
    cl.pop(k)
cl.update(action="cancel", refund=M("64750.00")); cancel_op.update(operation_id="bk_7Cx2", summary="Cancel Casa Mira, 27 Dec to 3 Jan. Refund INR 64,750.00 to your card within 5 days.")
put("valid", "booking-operation-cancel", cancel_op, "BookingOperation")
bad = copy.deepcopy(q); bad["quote_id"] = "qt_Sek1"; bad["currency"] = "SEK"
for l in bad["lines"]: l["amount"]["currency"] = "SEK"
for x in ("total",): bad[x]["currency"] = "SEK"
for p in bad["payment_schedule"]: p["amount"]["currency"] = "SEK"
for c in bad["cancellation"]: c["refund"]["currency"] = "SEK"
bad["deposit"]["amount"]["currency"] = "SEK"
put("valid", "quote-sek", dict(bad, signature=sign(bad, priv, "livstay-quote+jws")), "Quote", typ="livstay-quote+jws")
put("valid", "counter-request", {"total": M("120000.00"), "note": "Could you do 1,20,000 for the week?"}, "CounterRequest")
put("valid", "change-request", {"check_out": "2027-01-04"}, "ChangeRequest")
put("valid", "mismatch-report", {"facts_version": 9, "field": "facts.parking", "description": "Page says one car; facts say two."}, "MismatchReport")
bad_op = copy.deepcopy(op); bad_op["terms"]["livstay"]["total"] = M("119500.00")
put("invalid", "booking-terms-differ-from-quote", bad_op, "BookingOperation", "quote_binding")

json.dump({"revision": "0.2", "keys": "keys.json", "quote": "valid/quote.json", "fixtures": manifest},
          open(os.path.join(F, "manifest.json"), "w"), indent=2)
print(len(manifest), "fixtures")
