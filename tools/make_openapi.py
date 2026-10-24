"""Generates openapi/livstay-0.2.yaml (OpenAPI 3.1). Run: python3 tools/make_openapi.py"""
import os, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "../schemas/livstay-0.2.schema.json#/$defs/"
ref = lambda n: {"$ref": S + n}
js = lambda n: {"content": {"application/json": {"schema": ref(n)}}}
def resp(code, desc, n=None, more=None):
    r = {"description": desc, "headers": {"LivStay-Revision": {"$ref": "#/components/headers/LivStayRevision"}}}
    if n: r.update(js(n))
    return {str(code): r, **(more or {})}
ERR = lambda *codes: {str(c): {"$ref": "#/components/responses/Error"} for c in codes}
REV = {"$ref": "#/components/parameters/LivStayRevision"}
P = lambda name, where="path", req=True, schema=None, desc=None: {k: v for k, v in {"name": name, "in": where, "required": req, "schema": schema or {"type": "string"}, "description": desc}.items() if v is not None}
PUB, SES = [{}], [{"session": []}]
ACC = lambda *sc: [{"account": list(sc)}]
def op(opid, summary, sec, params=None, body=None, responses=None, sect=None):
    o = {"operationId": opid, "summary": summary, "security": sec, "parameters": [REV] + (params or []), "responses": responses}
    if sect: o["description"] = f"Spec {sect}."
    if body: o["requestBody"] = {"required": True, **js(body)}
    return o
idem = P("Idempotency-Key", "header")
paths = {
 "/homes": {"get": op("listHomes", "List Homes", PUB, [P("near", "query", False), P("radius_km", "query", False, {"type": "integer"}),
    P("area", "query", False), P("check_in", "query", False, {"type": "string", "format": "date"}),
    P("check_out", "query", False, {"type": "string", "format": "date"}), P("adults", "query", False, {"type": "integer", "minimum": 1}),
    P("children_ages", "query", False, desc="Comma-separated ages 0-17"), P("pets", "query", False, {"type": "integer", "minimum": 0}),
    P("cursor", "query", False)], None, {**resp(200, "A page of Homes", "HomesPage"), **ERR(400)}, "§6.1")},
 "/homes/{home_id}": {"get": op("getHome", "Get a Home", PUB, [P("home_id")], None, {**resp(200, "The Home", "Home"), **ERR(400, 404)}, "§6.1")},
 "/homes/{home_id}/availability": {"get": op("getAvailability", "Availability", PUB, [P("home_id"),
    P("from", "query", True, {"type": "string", "format": "date"}), P("to", "query", True, {"type": "string", "format": "date"})],
    None, {**resp(200, "Availability", "Availability"), **ERR(400, 404)}, "§7.1")},
 "/homes/{home_id}/quotes": {"post": op("createQuote", "Get a binding Quote", PUB, [P("home_id")], "QuoteRequest",
    {**resp(201, "A signed Quote", "Quote"), **ERR(400, 404, 409, 429)}, "§7.2")},
 "/quotes/{quote_id}": {"get": op("getQuote", "Get a kept Quote", PUB, [P("quote_id")], None, {**resp(200, "The Quote", "Quote"), **ERR(404)}, "§7.2")},
 "/homes/{home_id}/mismatch": {"post": op("reportMismatch", "Report a Fact or Quote that does not match", SES, [P("home_id")],
    "MismatchReport", {"202": {"description": "Accepted"}, **ERR(400, 401, 404)}, "§6.6")},
 "/tier-issuers": {"get": op("listTierIssuers", "Accepted tier credential issuers", PUB, None, None,
    {"200": {"description": "Issuers", "content": {"application/json": {"schema": {"type": "object", "properties": {"issuers": {"type": "array", "items": {"type": "string"}}}}}}}}, "§13.6")},
 "/bookings": {
   "get": op("listBookings", "The traveller's bookings", ACC("poppy:read"), [P("cursor", "query", False)], None, {"200": {"description": "Bookings"}, **ERR(401, 403)}, "§12.1"),
   "post": op("proposeBooking", "Propose a booking from a Quote", ACC("livstay:book"), [idem], "BookingRequest",
     {"202": {"description": "A proposed booking operation", "content": {"application/json": {"schema": {"type": "object", "required": ["operation"], "properties": {"operation": ref("BookingOperation")}}}}},
      **ERR(400, 401, 403, 404, 409, 429)}, "§9.1")},
 "/bookings/{booking_id}": {"get": op("getBooking", "One booking", ACC("poppy:read"), [P("booking_id")], None, {"200": {"description": "The booking"}, **ERR(401, 403, 404)}, "§12.1")},
 "/bookings/completion/{operation_id}": {"get": op("getCompletion", "Completion record: payment and identity steps", ACC("poppy:read"),
    [P("operation_id")], None, {**resp(200, "Completion", "Completion"), **ERR(401, 403, 404)}, "§9.5")},
 "/bookings/{operation_id}/counter": {"post": op("counterBooking", "Counter a proposed booking", ACC("livstay:book"), [P("operation_id"), idem],
    "CounterRequest", {"200": {"description": "The operation, unchanged or revised"}, **ERR(400, 401, 403, 404, 409)}, "§10.2")},
 "/bookings/{booking_id}/events": {"get": op("getBookingEvents", "Booking event feed", ACC("poppy:read"),
    [P("booking_id"), P("cursor", "query", False), P("wait", "query", False, {"type": "integer", "minimum": 0, "maximum": 30})],
    None, {**resp(200, "Events", "EventsPage"), **ERR(401, 403, 404)}, "§12.2")},
 "/bookings/{booking_id}/contact": {
   "get": op("getContact", "Contact sharing state", ACC("poppy:read"), [P("booking_id")], None, {**resp(200, "State", "ContactState"), **ERR(401, 403, 404)}, "§12.4"),
   "put": op("shareContact", "Share contact details with the Host", ACC("livstay:share_contact"), [P("booking_id")], "ContactRequest",
     {**resp(200, "Shared", "ContactState"), **ERR(400, 401, 403, 404)}, "§12.4"),
   "delete": op("revokeContact", "Stop sharing contact details", ACC("livstay:share_contact"), [P("booking_id")], None,
     {**resp(200, "Revoked", "ContactState"), **ERR(401, 403, 404)}, "§12.4")},
 "/bookings/{booking_id}/changes": {"post": op("changeBooking", "Propose a change", ACC("livstay:book"), [P("booking_id"), idem], "ChangeRequest",
    {"202": {"description": "A change operation"}, **ERR(400, 401, 403, 404, 409)}, "§12.5")},
 "/bookings/{booking_id}/cancellation": {"post": op("cancelBooking", "Propose a cancellation", ACC("livstay:book"), [P("booking_id"), idem], None,
    {"202": {"description": "A cancel operation"}, **ERR(401, 403, 404, 409)}, "§12.5")},
}
doc = {"openapi": "3.1.0",
 "info": {"title": "LivStay", "version": "0.2",
          "description": "LivStay draft 0.2 (extension livstay.org/stays). Paths are relative to the extension's `endpoint`. Bookings use the Poppy operations extension for confirm, track and cancel; conversations use Poppy's own endpoints. Schemas: ../schemas/livstay-0.2.schema.json.",
          "license": {"name": "Apache-2.0", "identifier": "Apache-2.0"}},
 "jsonSchemaDialect": "https://json-schema.org/draft/2020-12/schema",
 "servers": [{"url": "{endpoint}", "variables": {"endpoint": {"default": "https://stay.example/livstay/v0"}}}],
 "paths": paths,
 "components": {
   "securitySchemes": {
     "session": {"type": "http", "scheme": "DPoP", "description": "A Poppy Session Token, signed out or in, with a DPoP proof. No scope required."},
     "account": {"type": "oauth2", "description": "A signed-in Poppy Session Token with the listed account scopes, sent with DPoP.",
                 "flows": {"authorizationCode": {"authorizationUrl": "https://stay.example/authorize", "tokenUrl": "https://stay.example/token",
                    "scopes": {"poppy:read": "Read bookings", "livstay:book": "Book, change and cancel stays you approve",
                               "livstay:share_contact": "Give the host your phone number and email",
                               "livstay:share_trip_context": "Tell the host the purpose of your trip and when you arrive"}}}}},
   "parameters": {"LivStayRevision": {"name": "LivStay-Revision", "in": "header", "required": False,
                  "schema": {"type": "string", "pattern": r"^\d+\.\d+$"}, "description": "The LivStay revision to answer in (§4.3). Agents MUST send it."}},
   "headers": {"LivStayRevision": {"schema": {"type": "string"}, "description": "The revision this response is in (§4.3)."}},
   "responses": {"Error": {"description": "A LivStay or Poppy error (§14)", **js("Error")}}}}
open(os.path.join(ROOT, "openapi", "livstay-0.2.yaml"), "w").write("# Generated by tools/make_openapi.py. Edit that file, not this one.\n" + yaml.safe_dump(doc, sort_keys=False, width=110))
print(len(paths), "paths")
