# Introduction

LivStay is an open protocol that lets a personal agent find an independent home, ask its host a question and book it, on the host's own terms, with no travel platform in the middle.

It is written as an extension to the [Personal Agent Protocol](https://personalagentprotocol.org/docs/introduction) (Poppy) draft 0.2. Poppy already defines how an agent discovers a company, signs a person in, holds a session, talks to the company and confirms an action before the company performs it. LivStay adds only what is specific to stays: the home, its facts, its availability, its terms, its protection, and how a booking is proposed, approved and confirmed.

## Why it exists

Travellers increasingly ask an AI assistant where to stay before they open any booking site. An assistant can only recommend what it can read, and only book what it can price and reserve reliably. Today that means the large travel platforms, because they are the only inventory agents can work with. Independent hosts, who rent a villa, a flat or a guesthouse they own or manage, have no standard way to be read, asked or booked by an agent.

LivStay gives them one, and gives agents a single interface to every host platform that implements it.

## What an agent can do

| Step | What happens | Section |
| --- | --- | --- |
| **Find** | Read `poppy.json`, list homes, read each home's facts, terms and protection. No sign-in. | [§6](specification.html#6-the-home) |
| **Price** | Get a signed quote for exact dates and party. The price is binding for 24 hours. | [§7](specification.html#7-availability-and-quotes) |
| **Ask** | Put the traveller's question to the host, a person, in a Poppy conversation. | [§8](specification.html#8-enquiries) |
| **Book** | Propose a booking. The calendar is held for 15 minutes while the traveller approves the exact terms. | [§9](specification.html#9-bookings) |
| **Stay** | Receive updates, change or cancel. Every write returns a signed receipt. | [§12](specification.html#12-after-booking) |

## Four levels

A host platform starts with what it has and adds the rest later.

| Level | Name | An agent can | Needs |
| --- | --- | --- | --- |
| 0 | Listed | Read homes, facts, terms and protection | Static files |
| 1 | Priced | Read availability and get binding quotes | A pricing endpoint |
| 2 | Reachable | Ask the host questions | Poppy conversations |
| 3 | Bookable | Book, change and cancel | Poppy sign-in and the `operations` extension |

Level 0 is what gets a home recommended. Publish it first.

## Principles

- **Recommendation before booking.** Facts the host stands behind are served to agents and on the home's public page, so an assistant that never calls the API cites the same statements.
- **The traveller approves, and the price is binding.** Every booking needs the traveller's own approval of its exact terms. The price on the quote is the price charged.
- **The host's rules hold on every channel.** Agents see the host's published terms, the same everywhere.
- **A person where it matters.** Enquiries reach the host as a human, and their answers can be cited.
- **Reuse, don't reinvent.** Identity, sessions, conversations and confirm-before-act are Poppy's.

## Who it is for

- **Host platforms**: property management systems, booking engines, channel managers, and hosts with their own sites. Start with the [host platform guide](guide-host-platforms.html).
- **Agent builders**: anyone building an assistant that plans or books travel. Start with the [agent guide](guide-agents.html).

## Status

This is draft 0.1. It will change as implementers learn, and until 1.0 a revision can break compatibility with earlier drafts. [LivAround](https://livaround.com) is the reference implementation, with a pilot in North Goa. See the [path to 1.0](path-to-1.html).

LivStay is an independent project. It is designed to work with the Personal Agent Protocol and is not affiliated with or endorsed by that protocol's authors or partners.
