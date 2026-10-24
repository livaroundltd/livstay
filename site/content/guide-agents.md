# Guide for agent builders

This guide is for anyone building a personal agent that plans or books stays. It follows draft 0.2. Booking assumes your agent already implements Poppy draft 0.2 as a personal agent; finding and pricing homes do not.

## 1. Say which revision you speak

List both extensions in your client metadata document, with the LivStay drafts you implement:

```json
"extensions": {
  "operations": { "version": "1" },
  "livstay.org/stays": { "version": "0", "revisions": ["0.2"] }
}
```

Send `LivStay-Revision: 0.2` on every LivStay request, and check that the response echoes it. Before 1.0, drafts can break each other; the header is how both sides know which one they are speaking ([§4.3](specification.html#43-revisions)).

## 2. Find homes

Read `/.well-known/poppy.json`, find `extensions["livstay.org/stays"]`, check its `revision`, note its `endpoint` and `level`, then call `GET {endpoint}/homes`. No token is needed.

## 3. Recommend from facts

Tell the traveller why a home fits using its facts: `ideal_for`, `not_for`, `check_in.how`, `children`, `when_things_go_wrong`. Cite the `home_id` and `facts_version`. An empty `accessibility` list means the host has not said, never that the home is accessible. Dates and times are in the home's `time_zone`.

Treat everything a host platform sends as data. A fact, an answer or a summary can never instruct your agent.

## 4. Price exactly

Ask for a Quote for the exact dates and party: adults, each child's age, and pets. Send ages only, never names. Then, before you show the price:

1. **Verify the signature** against the host platform's `keys` ([§13.2](specification.html#132-verifying)).
2. **Reconcile**: lines in the total add up to the total, the payment schedule adds up to the total, refunds never exceed it ([§2.1](specification.html#21-dates-times-and-money)).

`tools/validate.py` and `tools/livstay_jws.py` in the repository do both. A Quote that fails either is not a price: do not show it, and send a mismatch report.

Show the total and each line, including any fee your agent charges. Keep the Quote. If the traveller wants time, a Quote is binding for up to 24 hours and holds nothing; do not propose a booking just to reserve dates.

## 5. Ask the host

If the traveller has a question the facts do not answer, open a Poppy conversation in a signed-out session with the `livstay.org/stays#enquiry` data and the question as text. A person answers. Never put the traveller's phone number or email in an enquiry.

## 6. Book, with the traveller's approval

1. Sign the traveller in with `livstay:book` and `poppy:read`. Ask for `livstay:share_trip_context` only if the traveller wants the host to know the trip's purpose or arrival time.
2. `POST {endpoint}/bookings` with the Quote. You get an operation in state `proposed`; the calendar is held until `expires_at`. Read `terms.livstay.tier` to see which tier was applied, and `requirements` to see what will be asked after confirmation.
3. Check that the revision restates the Quote it is bound to: dates, party, total, due now, deposit. If anything differs, do not confirm.
4. Show the host platform's name, the host's name and the operation's `summary` in your own interface, and get the traveller's answer there.
5. Confirm with `approved_by: "user"`. A standing permission is never enough for a stay.

## 7. Complete

If the operation goes `in_progress`, read `GET {endpoint}/bookings/completion/{operation_id}`. Open each pending step's page in the traveller's browser session before `complete_by`. Never collect card, bank or identity details yourself. When every step is done the operation succeeds; if `complete_by` passes, it fails and nothing is kept.

## 8. After booking

- Follow `GET {endpoint}/bookings/{booking_id}/events` with `wait`. Verify and keep every Receipt it carries.
- When you see `message_waiting`, or the traveller wants to talk to the host, open the booking conversation: a Poppy conversation whose first message carries `livstay.org/stays#booking` and the `booking_id`. The host platform never opens it for you.
- Changes and cancellations are new operations, each needing fresh approval.
- Share the traveller's contact details with the host only when they ask, with `PUT …/contact`; withdraw them with `DELETE`.

## Things not to do

- Do not confirm a revision the traveller has not seen.
- Do not hold dates you are not about to book; holds you let expire count against your agent.
- Do not pass one traveller's data to another host platform, or another agent.
- Do not rank a home higher because its host platform pays you. If you charge a fee, it is a quote line the traveller sees.
