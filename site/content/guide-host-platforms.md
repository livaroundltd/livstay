# Guide for host platforms

This guide takes a host platform from nothing to Level 3. Each level is useful on its own; stop wherever it makes sense.

## Before you start

- You need a domain you serve over HTTPS, and one calendar per home.
- Read the [specification](specification.html) sections listed at each step. Field tables there are normative; this guide is not.

## Level 0: Listed

The goal: an assistant reading your site or your files can describe each home accurately and say why it fits a traveller.

1. **Write each home's facts with its host.** Who it suits, who it does not, check-in and check-out, what is and isn't included, parking, pets, noise, backup power, house rules, cancellation in one sentence, and what the host does when something breaks. See [§6.2](specification.html#62-facts). Do not generate facts the host has not reviewed.
2. **Publish the home's public page** with those facts as HTML and schema.org `Accommodation` markup ([§6.5](specification.html#65-the-same-facts-on-the-web)).
3. **Serve the same data as JSON** at `GET {endpoint}/homes` and `GET {endpoint}/homes/{home_id}`. This can be a static file.
4. **Declare protection** for every home: who carries the risk, how claims are decided, and how fast ([§6.4](specification.html#64-protection)). A home without it is not published.
5. **Publish `poppy.json`** at `/.well-known/poppy.json` with the `livstay.org/stays` entry and `"level": 0`.

```json
{
  "protocol_version": "0.2",
  "organization": { "name": "Example Stays", "domain": "stays.example" },
  "web": {},
  "extensions": {
    "livstay.org/stays": {
      "version": "0",
      "endpoint": "https://stays.example/livstay/v0",
      "level": 0
    }
  }
}
```

**Check:** the facts in your JSON and on your page match, field by field. Run that check on every edit.

## Level 1: Priced

1. **Availability.** `GET {endpoint}/homes/{home_id}/availability` from your calendar, with per-night price and stay rules ([§7.1](specification.html#71-availability)).
2. **Signing keys.** Generate a signing key pair, publish the public key as a JWK Set and list it in `keys`.
3. **Quotes.** `POST {endpoint}/homes/{home_id}/quotes` returns a signed quote with every fee as its own line, valid for up to 24 hours ([§7.2](specification.html#72-quotes)).
4. **Honour quotes.** Store every quote. A booking proposed from an unexpired quote is charged its `total` or fails with `dates_unavailable`. It is never repriced.

**Check:** change a rate after issuing a quote, then book from the quote. The old price must hold.

## Level 2: Reachable

1. **Poppy basics.** Implement Poppy Sessions: an OAuth server at `auth.issuer`, client assertions, session tokens and DPoP. Signed-out sessions are enough for enquiries.
2. **Conversations.** Implement Poppy conversations and route each enquiry to the host as a person ([§8](specification.html#8-enquiries)). Host replies have `sender: "human"`.
3. **Scope.** Add `livstay:enquire` to `auth.custom_scopes` with a plain description.
4. **Reply times.** Tell agents when to expect an answer, from the host's real median reply time.

**Check:** send an enquiry, answer it from the host's phone, and confirm the agent sees `responder: "human"`.

## Level 3: Bookable

1. **Sign-in.** Add Poppy Direct Sign-In. Bookings need a signed-in session.
2. **Operations.** Implement the Poppy `operations` extension version `"1"`: proposed, confirmed, tracked and cancelled operations, executed at most once.
3. **Bookings.** `POST {endpoint}/bookings` turns a quote into a proposed booking operation and holds the calendar for up to 15 minutes ([§9](specification.html#9-bookings)). Set `user_approval_required: true` whenever money moves, and write a `summary` a traveller can decide from.
4. **Requests and counters**, if any home is not instant-book ([§10](specification.html#10-requests-and-counter-offers)). A host counter can only be kinder than the published terms.
5. **Payment.** On confirmation, send the traveller to your own payment page in their browser session ([§11](specification.html#11-payment)).
6. **After booking.** Open one conversation per booking for updates, and return a signed receipt for every write ([§12](specification.html#12-after-booking), [§13.1](specification.html#131-receipts)).
7. **Limits.** Cap open holds per traveller and per agent ([§15.3](specification.html#153-calendar-denial-of-service)).

**Check:** confirm the same operation twice and see one booking; let a hold expire and see the dates released and nothing charged.

## What hosts should see

Every action an agent takes appears on the booking as the host would describe it: who booked, through which agent, what was approved, and the receipt. Hosts should never have to read JSON to know what happened.
