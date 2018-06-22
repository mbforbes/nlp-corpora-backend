# nlp-corpora-backend

This repository contains the infrastructure to provide a live status of
`/projects/nlp-corpora/` by crawling its contents.

## Contributing

Current feature worklist:

- [ ] Badge showing how recently checker job was run

- [ ] Ensure email sends on problems

- [ ] If possible, color code the check / cross marks

- [ ] Transition to single check/cross in table. Have single report
  (overwritten at each run) with details.

- [ ] Expand checks:

    - [ ] Owner checks (TODO: should only be admins?)

    - [ ] Permissions checks (TODO: )

    - [ ] `g+s` (i.e., `chmod g+s directory/`) permissions: do we need it on
      all directories (not just top-level ones), and if so, include in
      permissions checks.

- [ ] Better docs: Copy corpus directories' `README.md`s into here (under
  corpus names) and link on status table so that all docs can be browsed from
  this master README.md

- [ ] Overall usage

    - [ ] Pie chart showing overall usage breakdown

    - [ ] Fail overall check (+ email) if usage gets above threshold (e.g., 95%)

- [ ] Migrate this to `uwnlp` github

- [ ] Send announcement
