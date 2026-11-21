# Proposal: Finders and Referrals

Status: **proposal**, not part of a numbered draft. Discussion: [#7](https://github.com/livaroundltd/livstay/issues/7).
It is written as the specification text it would become when folded into a draft: a new party in
§3.1, one new Terms field (§6.3), new §6.7 and §13.7, additions to §15 and Appendix C. Section
numbers follow `spec/livstay-0.2.md`. It is purely additive: a Home without `terms.referral`, and
a Host Platform that ignores `livstay_ref`, are unchanged.

Why: a Home's page is its Host Platform's own page (§6.5, `url`). Anyone who sends a traveller
there (a directory such as homes.livstay.org, a travel site, a newsletter) needs a way to be
credited that every Host Platform can check for itself, without a shared database. A Quote
already does this for an agent that prices a stay. A Referral does it for a finder that only
sends the traveller to the page.

---

## Changes to §3.1 The parties

Add after the diagram:

> A **Finder** sends a traveller to a Home's `url` without pricing or booking the stay: a
> directory, a travel site, an editor. A Finder is credited through a Referral (§6.7). A
> Personal Agent that books from a Quote is credited by the Quote and needs no Referral.

## New Terms field (§6.3)

| Field | Req. | Description |
| --- | --- | --- |
| `referral` | No | What the Host Platform pays a Finder for a booking it referred: `{ "percent", "basis", "window_days", "finders" }`. `percent` is an integer. `basis` is `total` (everything the traveller pays for the stay, taxes included, deposits excluded) or `total_excl_tax`. `window_days` is an integer from 1 to 90. `finders` is an array of Finder origins whose Referrals the Host Platform accepts, or `["*"]` for any Finder that publishes keys. Absent: the Home accepts no Referrals. |

Like every other Term, `referral` is the same for every Finder and for every agent, and is bound
into a Quote by `terms_version`.

## New §6.7 Referrals

A Referral is a signed object (§13.1) that a Finder issues for one Home and one traveller visit,
and that the Home's Host Platform verifies and keeps.

### 6.7.1 Issuing

A Finder **MAY** issue a Referral only for a Home whose Terms have a `referral` member that lists
the Finder's origin or `"*"`. It issues one when the traveller follows a link to the Home, and
sends the traveller to the Home's `url` with the Referral in the query parameter `livstay_ref`:

```
https://booking.example.com/casa-mira?livstay_ref=eyJhbGciOiJFUzI1NiIsImtpZCI6ImYxIiwidHlwIjoibGl2c3RheS1yZWZlcnJhbCtqd3MifQ...
```

| Claim | Req. | Description |
| --- | --- | --- |
| `iss` | Yes | The Finder's origin, e.g. `https://homes.livstay.org`. |
| `ref_id` | Yes | Prefixed `ref_`, at least 128 bits of randomness. Unique per issue. |
| `home_id` | Yes | The Home. |
| `iat` | Yes | Integer seconds since the epoch. |
| `exp` | Yes | `iat` plus the Home's `window_days`, in seconds. |

A Referral **MUST NOT** carry anything about the traveller: no name, contact, device or account
identifier. It says only who sent someone to which Home, and when.

### 6.7.2 Verifying and keeping

On receiving `livstay_ref` on a Home's page, the Host Platform:

1. verifies the Referral as §13.2 describes, with `typ` `livstay-referral+jws`, against the
   Finder's keys (§13.7) for `iss`;
2. rejects it unless `home_id` is this Home, `iss` is accepted by the Home's `referral.finders`,
   and `iat <= now < exp`;
3. keeps it for the traveller on its own origin until `exp`, for example in a first-party cookie
   scoped to that Home. It **MUST NOT** extend `exp`.

A rejected Referral is ignored: the page works as if it were absent, and the traveller is not told.

If a traveller holds more than one valid Referral for a Home, the most recently issued applies.
A booking made from a Quote (§7.2, §9.1) is the agent's, and no Referral applies to it.

### 6.7.3 Bookings under a Referral

A booking of the Home that succeeds while the traveller holds a valid Referral is a **referred
booking**. The Host Platform:

- **MUST** record the Referral's `ref_id` and `iss` on the booking, and keep the Referral as it
  keeps Quotes (§13.4);
- owes the Finder `referral.percent` of the `basis`, as the Terms in force when the booking was
  made stated it, less the same share of any amount later refunded to the traveller;
- **MUST NOT** charge the traveller for it. A Finder's fee is paid by the Host Platform or the
  Host, never added to the traveller's price. It is not a Quote line (§7.2, "Fees are lines").

How the Host Platform reports referred bookings to a Finder and settles the fee is agreed between
them. A machine-readable report is an open topic (Appendix C).

## New §13.7 Finder keys

A Finder publishes a JWK Set at `{iss}/.well-known/livstay-finder-keys.json`, following §13.4 for
key format, rotation, retirement and compromise. A Finder's keys sign only Referrals; a Host
Platform **MUST NOT** accept a Referral signed with a Host Platform key, or a Quote signed with a
Finder key.

## Security and privacy (§15)

Add to §15.5 Traveller data:

> A Referral identifies a visit, not a person (§6.7.1). A Host Platform keeps it only on its own
> origin and only until it expires.

Add a new §15.8 Referral abuse:

> A Referral is a bearer token for a Finder's credit, not for anything a traveller can use. A copied
> Referral can at most credit its Finder for a booking that Finder did not cause; Host Platforms
> **MAY** require that a Referral be first seen within minutes of its `iat`, and **SHOULD** watch for
> one `ref_id` appearing on many bookings.

## Appendix C, add

- **Referral reporting.** A signed report of referred bookings and refunds, from Host Platform to
  Finder, so a fee can be settled without a private agreement per pair.

## Changes list, when folded into a draft

- **Finders and Referrals.** A Home may state what it pays whoever sends a traveller to its page
  (`terms.referral`). Finders issue signed Referrals (`livstay-referral+jws`) under their own keys;
  Host Platforms verify and keep them, and record them on referred bookings (§6.7, §13.7).

---

## How LivAround would implement it (illustrative, not normative)

- **As a Finder:** homes.livstay.org issues Referrals with its own key and sends each Home's
  visitors to its `url`.
- **As a Host Platform:** every LivAround Home states
  `{ "percent": 5, "basis": "total", "window_days": 30, "finders": ["https://homes.livstay.org"] }`.
  A booking under a valid Referral is treated exactly like a booking from a Quote; a booking
  without one is the host's own, at the host's own rate.
