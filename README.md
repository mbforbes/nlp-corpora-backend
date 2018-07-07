# nlp-corpora-backend

This repository contains the infrastructure to provide a live status of
`/projects/nlp-corpora/` by crawling its contents.

## Installation

```bash
# create a fresh virtualenv. I use pyenv. You can use whatever.
# Use python >= 3.6.5. Then:
pip install -r requirements.txt
```

## Running

```bash
# also prints log to stderr if any cheks failed. (This behavior so cron
# auto sends an email to you if anything fails, but not if things pass.)
python check.py \
    --directory /projects/nlp-corpora/ \
    --out-file out.md \
    --log-file log.txt

# To run on the test directories (sorry Nelson, no automated tests yet), I run
# this to ignore the output markdown and see only the log.
python check.py \
    --directory test/test-nlp-corpora/ \
    --ok-owners max \
    --group-config test/test-groups.json \
    --out-file /dev/null

```

## Contributing

Current feature worklist:

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
