# Contributing to LivStay

LivStay is a draft, and it changes based on what implementers learn.

## Feedback

Open an issue for:

- a gap, or a part that does not work as written;
- something that could be simpler or removed;
- privacy, security or money-handling concerns;
- how hosts actually describe and rent their homes, where the draft gets it wrong.

Name the section (for example `§9.3`) and, where you can, say what you would change.

## Changes to the specification

- Small fixes (typos, broken examples, unclear wording): open a pull request.
- Anything that changes behaviour: open an issue first, so the change can be discussed before it is written.
- Keep the specification's conventions: BCP 14 key words, field tables with a `Req.` column, examples captioned and marked illustrative.
- If a change touches Poppy, check it against the current Poppy draft. Where Poppy defines something, LivStay defers to it.

## The website

Docs content lives in `site/content/` and the specification in `spec/`. Run `python3 tools/build_site.py` to check the site builds.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
