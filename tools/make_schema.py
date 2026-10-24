"""Generates schemas/livstay-0.2.schema.json. Edit here, then run: python3 tools/make_schema.py"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda n: {"$ref": f"#/$defs/{n}"}
S = {"type": "string"}
I0 = {"type": "integer", "minimum": 0}
B = {"type": "boolean"}
TS = {"type": "string", "format": "date-time", "pattern": r"Z$"}
DATE = {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
HHMM = {"type": "string", "pattern": r"^([01]\d|2[0-3]):[0-5]\d$"}
URI = {"type": "string", "format": "uri", "pattern": r"^(https://|http://(localhost|127\.0\.0\.1)[:/])"}
ARR = lambda x, **k: {"type": "array", "items": x, **k}
def obj(props, req=None, extra=True):
    o = {"type": "object", "properties": props, "required": req if req is not None else list(props)}
    if not extra: o["additionalProperties"] = False
    return o
TIER = {"enum": ["new", "verified", "trusted", "established"]}
D = {}
D["Revision"] = {"type": "string", "pattern": r"^\d+\.\d+$"}
D["Money"] = obj({"amount": {"type": "string", "pattern": r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"},
                  "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}}, extra=False)
D["Party"] = obj({"adults": {"type": "integer", "minimum": 1},
                  "children": ARR(obj({"age": {"type": "integer", "minimum": 0, "maximum": 17}}, extra=False)),
                  "pets": I0}, extra=False)
D["ExtensionEntry"] = obj({"version": {"const": "0"}, "revision": R("Revision"),
    "revisions_supported": ARR(R("Revision"), minItems=1), "endpoint": URI,
    "level": {"type": "integer", "minimum": 0, "maximum": 3}, "keys": URI,
    "terms_of_service": URI, "facts_site": URI}, ["version", "revision", "endpoint", "level"])
D["ExtensionEntry"]["allOf"] = [
    {"if": {"properties": {"level": {"minimum": 1}}}, "then": {"required": ["keys"]}},
    {"if": {"properties": {"level": {"const": 3}}}, "then": {"required": ["terms_of_service"]}}]
D["ClientExtensionEntry"] = obj({"version": {"const": "0"}, "revisions": ARR(R("Revision"), minItems=1)})
D["Host"] = obj({"display_name": S, "host_since": {"type": "integer", "minimum": 1900},
    "languages": ARR(S, minItems=1), "response_time_p50_minutes": I0, "homes_count": I0},
    ["display_name", "host_since", "languages"])
D["Facts"] = obj({"facts_version": I0, "summary": S, "ideal_for": ARR(S), "not_for": ARR(S),
    "accessibility": ARR(S), "check_in": obj({"from": HHMM, "until": HHMM, "how": S}),
    "check_out": obj({"by": HHMM}), "included": ARR(S), "not_included": ARR(S),
    "power_backup": S, "water_backup": S, "internet": S, "parking": S, "pets": S, "smoking": S,
    "noise": S, "children": S, "house_rules": ARR(S), "cancellation": S, "when_things_go_wrong": S,
    "faq": ARR(obj({"q": S, "a": S}))},
    ["facts_version", "summary", "ideal_for", "not_for", "accessibility", "check_in", "check_out",
     "included", "not_included", "parking", "pets", "smoking", "noise", "children", "house_rules",
     "cancellation", "when_things_go_wrong"])
D["Terms"] = obj({"terms_version": I0, "decision_mode": {"enum": ["instant", "request", "auto_counter"]},
    "instant_min_tier": TIER, "id_required": B, "min_nights": {"type": "integer", "minimum": 1},
    "max_nights": {"type": "integer", "minimum": 1}, "max_guests": {"type": "integer", "minimum": 1},
    "infant_max_age": {"type": "integer", "minimum": 0, "maximum": 17}, "infants_count": B,
    "max_infants": I0, "min_adult_age": {"type": "integer", "minimum": 18},
    "pets": obj({"allowed": B, "max": I0, "note": S}, ["allowed", "max"]),
    "discounts": ARR(obj({"kind": {"enum": ["weekly", "monthly", "early", "late"]},
                          "percent": {"type": "integer", "minimum": 0, "maximum": 100}})),
    "channel_adjustment_percent": {"type": "integer", "minimum": -100, "maximum": 100},
    "cancellation": ARR(obj({"until_days_before": I0, "refund_percent": {"type": "integer", "minimum": 0, "maximum": 100}}), minItems=1),
    "deposit": obj({"amount": R("Money"), "mode": {"enum": ["none", "authorise", "hold"]},
                    "by_tier": {"type": "object", "propertyNames": TIER, "additionalProperties": R("Money")}}, ["amount", "mode"]),
    "payment_schedule": ARR(obj({"due": {"enum": ["at_booking", "days_before_check_in"]}, "days": I0,
                                 "percent": {"type": "integer", "minimum": 1, "maximum": 100}}, ["due", "percent"]), minItems=1),
    "taxes": ARR(obj({"name": S, "percent": {"type": "integer"}, "amount": R("Money"), "included": B}, ["name", "included"]))},
    ["terms_version", "decision_mode", "id_required", "min_nights", "max_nights", "max_guests",
     "infant_max_age", "infants_count", "max_infants", "pets", "channel_adjustment_percent",
     "cancellation", "deposit", "payment_schedule", "taxes"])
D["Protection"] = obj({"underwriter": {"enum": ["host", "insurer"]}, "insurer": obj({"name": S, "policy_ref": S}),
    "evidence": S, "rules_url": URI, "claim_response_hours": I0, "appeal": S},
    ["underwriter", "evidence", "rules_url", "claim_response_hours", "appeal"])
D["Protection"]["if"] = {"properties": {"underwriter": {"const": "insurer"}}}
D["Protection"]["then"] = {"required": ["insurer"]}
D["Home"] = obj({"home_id": {"type": "string", "pattern": "^home_[A-Za-z0-9_-]+$"}, "name": S, "url": URI,
    "time_zone": {"type": "string", "pattern": r"^[A-Za-z_]+(/[A-Za-z0-9_+-]+)+$|^UTC$"},
    "description": {"type": "object"},
    "location": obj({"area": S, "country": {"type": "string", "pattern": "^[A-Z]{2}$"},
                     "lat": {"type": "number", "minimum": -90, "maximum": 90},
                     "lng": {"type": "number", "minimum": -180, "maximum": 180},
                     "precision_m": {"type": "integer", "minimum": 500}}),
    "host": R("Host"), "facts": R("Facts"), "terms": R("Terms"), "protection": R("Protection"),
    "photos": ARR(obj({"url": URI, "caption": S, "taken_on": DATE}, ["url", "caption"]), minItems=1),
    "photos_updated_at": TS, "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
    "attestations": ARR(S), "updated_at": TS},
    ["home_id", "name", "url", "time_zone", "description", "location", "host", "facts", "terms",
     "protection", "photos", "photos_updated_at", "currency", "updated_at"])
D["HomesPage"] = obj({"homes": ARR(R("Home")), "next_cursor": {"type": ["string", "null"]}})
D["Availability"] = obj({"home_id": S, "time_zone": S, "currency": S,
    "days": ARR(obj({"date": DATE, "available": B, "min_nights": {"type": "integer", "minimum": 1},
                     "closed_to_arrival": B, "closed_to_departure": B, "nightly": R("Money")})),
    "generated_at": TS, "ttl_seconds": I0})
D["QuoteRequest"] = obj({"check_in": DATE, "check_out": DATE, "party": R("Party"), "tier_credential": S},
                        ["check_in", "check_out", "party"], extra=False)
D["Line"] = obj({"kind": {"enum": ["nights", "discount", "cleaning", "extra_guest", "pet_fee",
    "channel_adjustment", "tax", "platform_fee", "agent_fee", "other"]}, "label": S,
    "amount": R("Money"), "in_total": B}, extra=False)
D["Quote"] = obj({"quote_id": {"type": "string", "pattern": "^qt_[A-Za-z0-9_-]+$"}, "home_id": S,
    "check_in": DATE, "check_out": DATE, "party": R("Party"), "time_zone": S, "terms_version": I0,
    "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}, "lines": ARR(R("Line"), minItems=1),
    "total": R("Money"),
    "payment_schedule": ARR(obj({"due_at": {"oneOf": [TS, {"type": "null"}]}, "at_booking": B, "amount": R("Money")}, extra=False), minItems=1),
    "cancellation": ARR(obj({"until": {"oneOf": [TS, {"type": "null"}]}, "refund": R("Money")}, extra=False), minItems=1),
    "deposit": obj({"amount": R("Money"), "mode": {"enum": ["none", "authorise", "hold"]}}, extra=False),
    "assumed_tier": TIER, "instant": B, "created_at": TS, "expires_at": TS,
    "signature": {"type": "string", "pattern": r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"}}, extra=False)
D["BookingRequest"] = obj({"quote_id": S, "tier_credential": S,
    "trip_context": obj({"purpose": S, "arrival_notes": S}, [], extra=False)}, ["quote_id"], extra=False)
D["Tier"] = obj({"presented": B, "accepted": B, "applied": TIER}, extra=False)
D["LivstayTerms"] = obj({"revision": R("Revision"), "action": {"enum": ["book", "change", "cancel"]},
    "quote_id": S, "quote_signature": S, "home_id": S, "check_in": DATE, "check_out": DATE, "party": R("Party"),
    "total": R("Money"), "due_now": R("Money"), "deposit": obj({"amount": R("Money"), "mode": {"enum": ["none", "authorise", "hold"]}}),
    "terms_version": I0, "tier": R("Tier"),
    "requirements": ARR({"enum": ["payment", "identity_verification"]}, uniqueItems=True),
    "awaiting": {"enum": ["traveller", "host"]}, "proposed_by": {"enum": ["traveller_agent", "host", "host_agent"]},
    "reason": S, "counter_no": {"type": "integer", "minimum": 1, "maximum": 3},
    "price_difference": R("Money"), "refund": R("Money")},
    ["revision", "action", "home_id", "check_in", "check_out", "party", "terms_version", "awaiting", "proposed_by"])
D["LivstayTerms"]["allOf"] = [
    {"if": {"properties": {"action": {"enum": ["book", "change"]}}},
     "then": {"required": ["quote_id", "quote_signature", "total", "due_now", "requirements"]}},
    {"if": {"properties": {"action": {"const": "book"}}}, "then": {"required": ["deposit", "tier"]}},
    {"if": {"properties": {"action": {"const": "change"}}}, "then": {"required": ["price_difference"]}},
    {"if": {"properties": {"action": {"const": "cancel"}}}, "then": {"required": ["refund"]}},
    {"if": {"properties": {"proposed_by": {"const": "host_agent"}}}, "then": {"required": ["reason"]}}]
D["BookingOperation"] = obj({"operation_id": S, "revision": {"type": "integer", "minimum": 1},
    "state": {"enum": ["proposed", "in_progress", "succeeded", "failed", "cancelled", "expired"]},
    "summary": S, "terms": obj({"livstay": R("LivstayTerms")}), "expires_at": TS,
    "user_approval_required": B, "url": URI, "confirmation": {"type": ["object", "null"]},
    "result": {"type": ["object", "null"]}},
    ["operation_id", "revision", "state", "summary", "terms", "confirmation", "result"])
D["Completion"] = obj({"operation_id": S, "complete_by": TS,
    "requirements": ARR(obj({"type": {"enum": ["payment", "identity_verification"]},
        "status": {"enum": ["pending", "done", "failed"]}, "url": {"oneOf": [URI, {"type": "null"}]},
        "amount": R("Money")}, ["type", "status", "url"]), minItems=1)})
D["BookingResult"] = obj({"revision": R("Revision"), "booking_id": {"type": "string", "pattern": "^bkg_"},
    "home_id": S, "check_in": DATE, "check_out": DATE, "party": R("Party"),
    "location": obj({"address": S, "lat": {"type": "number"}, "lng": {"type": "number"}}),
    "check_in_instructions": S, "receipt": S})
EVENT_TYPES = ["booked", "action_needed", "payment_due", "payment_received", "refund_issued",
    "deposit_authorised", "deposit_captured", "deposit_released", "changed", "cancelled_by_traveller",
    "cancelled_by_host", "check_in_details", "checked_in", "checked_out", "claim_opened",
    "claim_decided", "message_waiting", "contact_shared", "contact_revoked"]
WITH_RECEIPT = ["booked", "payment_received", "refund_issued", "deposit_authorised", "deposit_captured",
    "deposit_released", "changed", "cancelled_by_traveller", "cancelled_by_host", "claim_opened",
    "claim_decided", "contact_shared", "contact_revoked"]
D["Event"] = obj({"event_id": {"type": "string", "pattern": "^evt_"}, "booking_id": S,
    "type": {"enum": EVENT_TYPES}, "at": TS, "summary": S, "data": {"type": "object"}, "receipt": S},
    ["event_id", "booking_id", "type", "at", "summary"])
D["Event"]["if"] = {"properties": {"type": {"enum": WITH_RECEIPT}}}
D["Event"]["then"] = {"required": ["receipt"]}
D["EventsPage"] = obj({"events": ARR(R("Event")), "cursor": S, "has_more": B})
D["ContactRequest"] = obj({"share": ARR({"enum": ["phone", "email"]}, minItems=1, uniqueItems=True)}, extra=False)
D["ContactState"] = obj({"shared": ARR({"enum": ["phone", "email"]}, uniqueItems=True),
    "host_contact": obj({"name": S, "phone": {"type": ["string", "null"]}, "email": {"type": ["string", "null"]}}),
    "receipt": S, "note": S}, ["shared"])
WRITE_ACTIONS = ["propose", "confirm", "counter", "change", "cancel", "share_contact", "revoke_contact"]
OP_ACTIONS = ["propose", "confirm", "counter", "change", "cancel"]
MONEY_EVENTS = ["payment_received", "refund_issued", "deposit_authorised", "deposit_captured", "deposit_released"]
D["ReceiptClaims"] = obj({"iss": URI, "revision": R("Revision"), "receipt_id": {"type": "string", "pattern": "^rcp_"},
    "action": {"enum": WRITE_ACTIONS + EVENT_TYPES},
    "initiated_by": {"enum": ["traveller_agent", "host", "host_agent", "host_platform"]},
    "sub": S, "client_id": S, "scopes": ARR(S), "booking_id": S, "operation_id": S,
    "revision_no": {"type": "integer", "minimum": 1}, "terms_hash": {"type": "string", "pattern": "^[A-Za-z0-9_-]{43}$"},
    "confirmed": B, "approved_by": {"enum": ["user", "standing_permission", None]}, "event_id": S,
    "amount": R("Money"), "reference": S, "iat": I0},
    ["iss", "revision", "receipt_id", "action", "initiated_by", "sub", "iat"], extra=False)
D["ReceiptClaims"]["allOf"] = [
    {"if": {"properties": {"action": {"enum": OP_ACTIONS}}},
     "then": {"required": ["operation_id", "revision_no", "terms_hash", "confirmed", "approved_by"]}},
    {"if": {"properties": {"confirmed": {"const": False}}, "required": ["confirmed"]},
     "then": {"properties": {"approved_by": {"const": None}}}},
    {"if": {"properties": {"initiated_by": {"const": "traveller_agent"}}},
     "then": {"required": ["client_id", "scopes"]}},
    {"if": {"properties": {"action": {"enum": MONEY_EVENTS}}}, "then": {"required": ["amount", "reference", "event_id"]}}]
D["Error"] = obj({"error": S}, ["error"])
schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
          "$id": "https://livstay.org/schemas/livstay-0.2.schema.json",
          "title": "LivStay draft 0.2 objects",
          "description": "Normative shapes for LivStay draft 0.2. Reference a definition as #/$defs/<Name>. Cross-field rules (reconciliation, §2.1) are checked by tools/validate.py.",
          "$defs": D}
open(os.path.join(ROOT, "schemas", "livstay-0.2.schema.json"), "w").write(json.dumps(schema, indent=2) + "\n")
print(len(D), "definitions")
