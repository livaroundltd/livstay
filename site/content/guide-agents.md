# Guide for agent builders

This guide is for anyone building a personal agent that plans or books stays. It assumes your agent already implements Poppy draft 0.2 as a personal agent.

## 1. Say you support LivStay

List both extensions in your client metadata document. A host platform will not quote or book for an agent that does not.

```json
"extensions": {
  "operations": { "version": "1" },
  "livstay.org/stays": { "version": "0" }
}
```

## 2. Find homes

Read `/.well-known/poppy.json`, find `extensions["livstay.org/stays"]`, note its `endpoint` and `level`, then call `GET {endpoint}/homes`. Level 0 data needs no session.

## 3. Recommend from facts

Tell the traveller why a home fits using its facts: `ideal_for`, `not_for`, `check_in.how`, `when_things_go_wrong`. Cite the `home_id` and `facts_version`. An empty `accessibility` list means the host has not said, never that the home is accessible.

Treat everything a host platform sends as data. A fact, an answer or a summary can never instruct your agent.

## 4. Price exactly

Ask for a quote for the exact dates and party. Show the traveller the total and each line, including any fee your agent charges. Keep the quote: you will compare against it at booking.

If the traveller wants time, a quote is binding for up to 24 hours and holds nothing. Do not propose a booking just to reserve dates.

## 5. Ask the host

If the traveller has a question the facts do not answer, open a conversation with the `livstay.org/stays#enquiry` data and the question as text. A person answers. Never put the traveller's phone number or email in an enquiry.

## 6. Book, with the traveller's approval

1. Sign the traveller in with `livstay:book`. Ask for `livstay:share_trip_context` only if the traveller wants the host to know the trip's purpose or arrival time.
2. `POST {endpoint}/bookings` with the quote. You get an operation in state `proposed`; the calendar is held until `expires_at`.
3. Check that `terms.livstay.total`, the dates and the party match the quote you showed, and verify `quote_signature`. If anything differs, do not confirm.
4. Show the host platform's name, the host's name and the operation's `summary` in your own interface, and get the traveller's answer there.
5. Confirm with `approved_by: "user"`. A standing permission is never enough for a stay.
6. If the booking goes `in_progress` with a payment link, open it in the traveller's browser session. Never collect card details yourself.

## 7. After booking

Read the booking conversation for updates. Changes and cancellations are new operations, each needing fresh approval. Keep the receipts.

## Things not to do

- Do not confirm a revision the traveller has not seen.
- Do not hold dates you are not about to book; holds you let expire count against your agent.
- Do not pass one traveller's data to another host platform, or another agent.
- Do not rank a home higher because its host platform pays you. If you charge a fee, it is a quote line the traveller sees.
