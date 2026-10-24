# Path to 1.0

LivStay is a draft. This page says how it becomes stable and what is deliberately unfinished.

## How we get there

- Anyone can build against the draft and send feedback.
- LivAround is implementing it as the reference host platform, with a pilot in North Goa.
- Draft 0.2 adds JSON Schemas, an OpenAPI document, fixtures, a validator and a Level 0–1 conformance runner. Independent host platforms should start there.
- We are looking for a second, independent host platform implementation and for agent builders to test against it.
- The spec changes based on what implementers learn. Until 1.0, a revision can break compatibility with earlier drafts.
- LivStay tracks the Personal Agent Protocol. When Poppy changes, LivStay follows.

## Feedback requested

- **Money:** whether quotes, holds and the approval rules are enough to make a stay price trustworthy.
- **Hosts:** whether the facts and terms objects capture how hosts actually describe and rent their homes.
- **Agents:** what an assistant needs that the draft does not give it.
- **Privacy and security:** traveller data, location, tier credentials, abuse of holds.
- **Simplification:** anything that could be removed.

## How to give feedback

- [Open an issue](https://github.com/livaroundltd/livstay/issues) in the spec repository. Contributions are made under the Apache License 2.0.
- Or write to the address on the [home page](../index.html).

## Open topics

These are left out on purpose and are not complete:

- **Conformance for Levels 2 and 3.** The runner covers Levels 0 and 1. Enquiries and bookings need a test personal agent with a Poppy client identity, sign-in and DPoP.

- **Payments.** LivStay uses a hosted payment page until Poppy defines payments, then adopts that.
- **Push.** Booking updates ride a conversation until Poppy defines push notifications.
- **Attachments.** Receipts and check-in packs as attachments, when Poppy defines them.
- **Multi-home stays.** One booking across linked homes, such as a villa and its cottage.
- **Search.** Whether listing homes needs a shared query vocabulary across host platforms.
- **Directory.** How agents find host platforms they do not already know.
- **Points and exchange.** Whether home swaps and points belong in a separate, member-only extension.

## Governance

LivStay was started by LivAround Ltd. The intent is to move the specification to a neutral home once there are independent implementations, so that no single host platform controls it.
