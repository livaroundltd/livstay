# Guide for host platforms

This guide takes a host platform from nothing to Level 3. Each level is useful on its own; stop wherever it makes sense. It follows draft 0.2.

## Before you start

- You need a domain you serve over HTTPS, and one calendar per home.
- Field tables in the [specification](specification.html) and the JSON Schemas in the repository are normative; this guide is not.
- Clone the [repository](https://github.com/livaroundltd/livstay). `tools/mock_host.py` is a working Level 1 host platform in one file, and `tools/conformance.py` checks yours.

## Level 0: Listed

The goal: an assistant reading your site or your API can describe each home accurately and say why it fits a traveller. No Poppy sessions, no tokens.

1. **Write each home's facts with its host.** Who it suits, who it does not, check-in and check-out times, what is and isn't included, parking, pets, children, noise, backup power, house rules, cancellation in one sentence, and what the host does when something breaks. See [§6.2](specification.html#62-facts). Do not generate facts the host has not reviewed.
2. **Set the home's time zone** (`Asia/Kolkata`, `Europe/Lisbon`). Every date and local time about the home is in it.
3. **Publish the home's public page** with those facts as HTML and schema.org `Accommodation` markup ([§6.5](specification.html#65-the-same-facts-on-the-web)).
4. **Serve the same data as JSON** at `GET {endpoint}/homes` and `GET {endpoint}/homes/{home_id}`, with no token, echoing the `LivStay-Revision` header ([§4.3](specification.html#43-revisions)).
5. **Declare protection** for every home ([§6.4](specification.html#64-protection)). A home without it is not published.
6. **Publish `poppy.json`** at `/.well-known/poppy.json`:

```json
{
  "protocol_version": "0.2",
  "organization": { "name": "Example Stays", "domain": "stays.example" },
  "web": {},
  "extensions": {
    "livstay.org/stays": {
      "version": "0",
      "revision": "0.2",
      "endpoint": "https://stays.example/livstay/v0",
      "level": 0
    }
  }
}
```

**Check:** `python3 tools/conformance.py https://stays.example` passes every `L0` check, and the facts in your JSON and on your page match, field by field.

## Level 1: Priced

Still no tokens. Quotes are public.

1. **List your API** in `poppy.json` `apis` (`openapi` pointing at your copy of `openapi/livstay-0.2.yaml`).
2. **Availability.** `GET {endpoint}/homes/{home_id}/availability` from your calendar ([§7.1](specification.html#71-availability)).
3. **Signing key.** Generate an ES256 (P-256) key pair in a key service, publish the public key as a JWK Set with `kid`, `use: "sig"` and `alg: "ES256"`, and list it in `keys` ([§13.4](specification.html#134-keys-and-retention)).
4. **Quotes.** `POST {endpoint}/homes/{home_id}/quotes` returns `201` and a signed Quote ([§7.2](specification.html#72-quotes)):
   - price from the whole party: adults, children's ages, pets;
   - round each line to the currency's minor unit, then make sure lines, total, payment schedule and refunds reconcile ([§2.1](specification.html#21-dates-times-and-money));
   - sign the canonical JSON of the Quote without `signature` ([§13.1](specification.html#131-signed-objects)). `tools/livstay_jws.py` does this in 40 lines.
5. **Honour and keep quotes.** A booking proposed from an unexpired Quote is charged its total or fails with `dates_unavailable`. Serve kept Quotes at `GET {endpoint}/quotes/{quote_id}`.

**Check:** every `L1` check passes, including signature and reconciliation. Then change a rate after issuing a Quote and book from it: the old price must hold.

## Level 2: Reachable

1. **Poppy sessions.** An OAuth server at `auth.issuer` that issues signed-out Session Tokens to agents (client assertions, DPoP). No sign-in yet.
2. **Conversations.** Implement Poppy conversations and list them in `agent.protocols`. Accept enquiries in signed-out sessions with no scope, and route each to the host as a person ([§8](specification.html#8-enquiries)). Host replies have `sender: "human"`.
3. **Reply times.** Tell agents when to expect an answer, from the host's real median reply time.
4. **Reports.** Accept mismatch reports ([§6.6](specification.html#66-reporting-a-mismatch)) and Poppy feedback.

**Check:** send an enquiry without signing in, answer it from the host's phone, and confirm the agent sees `responder: "human"`.

## Level 3: Bookable

1. **Sign-in and scopes.** Add Poppy Direct Sign-In, able to grant `poppy:read`, `livstay:book`, `livstay:share_contact` and `livstay:share_trip_context`, each described in `auth.custom_scopes`.
2. **Operations.** Implement the Poppy `operations` extension version `"1"`: proposed, confirmed, tracked and cancelled operations, executed at most once, never changed after confirmation.
3. **Bookings.** `POST {endpoint}/bookings` turns a Quote into a proposed booking operation and holds the calendar for up to 15 minutes ([§9](specification.html#9-bookings)). Report the tier outcome in `terms.livstay.tier`; set `user_approval_required: true` whenever money moves; write a `summary` a traveller can decide from.
4. **Completion.** On confirmation, create the completion record with a fixed `complete_by` and the payment and identity steps ([§9.5](specification.html#95-completion-payment-and-identity)). Succeed when every step is done; fail and release the dates when `complete_by` passes.
5. **Requests and counters**, if any home is not instant-book ([§10](specification.html#10-requests-and-counter-offers)). Each counter carries its own new Quote, and can only be kinder than the published terms.
6. **Events.** Serve each booking's event feed ([§12.2](specification.html#122-booking-events)), with a Receipt on every money movement, claim and host cancellation.
7. **Booking conversation.** Accept the conversation the agent opens for a booking; hold host messages and announce them with `message_waiting` until it does ([§12.3](specification.html#123-the-booking-conversation)).
8. **Contact.** `PUT`, `GET` and `DELETE` on `/bookings/{booking_id}/contact` ([§12.4](specification.html#124-contact)).
9. **Privacy and limits.** Delete trip context within 24 hours of a failed or abandoned proposal. Cap open holds per traveller and per agent ([§15.3](specification.html#153-calendar-denial-of-service)).

**Check:** confirm the same operation twice and see one booking; let `complete_by` pass and see the dates released and nothing charged; verify every Receipt in the feed against your `keys`.

## What hosts should see

Every action an agent takes appears on the booking as the host would describe it: who booked, through which agent, what was approved, what was paid, and the receipt. Hosts should never have to read JSON to know what happened.
