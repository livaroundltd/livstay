# LivStay

An open protocol for personal agents to find, ask about and book independent homes.

LivStay is an extension of the [Personal Agent Protocol](https://personalagentprotocol.org) (Poppy) draft 0.2, named `livstay.org/stays`. Poppy covers discovery, sign-in, sessions, conversations and confirm-before-act. LivStay adds what is specific to stays: the home, its facts, availability, binding quotes, terms, protection, enquiries to the host, and bookings the traveller approves.

**Status: draft 0.1.** Until 1.0, a revision can break compatibility with earlier drafts.

- Website: <https://livstay.org>
- Specification: [`spec/livstay-0.1.md`](spec/livstay-0.1.md)
- Guides: [host platforms](site/content/guide-host-platforms.md), [agent builders](site/content/guide-agents.md)
- Path to 1.0: [`site/content/path-to-1.md`](site/content/path-to-1.md)

## Levels

| Level | Name | An agent can |
| --- | --- | --- |
| 0 | Listed | Read homes, facts, terms and protection |
| 1 | Priced | Read availability and get binding quotes |
| 2 | Reachable | Ask the host questions |
| 3 | Bookable | Book, change and cancel |

## Repository layout

| Path | What |
| --- | --- |
| `spec/` | The normative specification, one file per draft |
| `site/` | Sources for livstay.org: the home page, styles and docs content |
| `tools/build_site.py` | Renders `site/` and `spec/` into `docs/` |
| `docs/` | The built site, served by GitHub Pages from `main` → `/docs`. Generated: edit `site/` or `spec/` and rebuild, never edit `docs/` by hand |
| `.github/workflows/pages.yml` | Checks that `docs/` matches its sources |

Build locally:

```sh
pip install markdown==3.10.3
python3 tools/build_site.py   # writes docs/; commit it with your change
python3 -m http.server -d docs 8000
```

## Implementations

- [LivAround](https://livaround.com): reference host platform, pilot in North Goa.

Building one? Open an issue and we will list it.

## Feedback

[Open an issue](https://github.com/livaroundltd/livstay/issues). See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache License 2.0](LICENSE). LivStay is an independent project. It is designed to work with the Personal Agent Protocol and is not affiliated with or endorsed by that protocol's authors or partners.
