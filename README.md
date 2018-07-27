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
    --out-file ~/repos/nlp-corpora/README.md \
    --log-file ~/repos/nlp-corpora/BUILD.txt \
    --doc-dir ~/repos/nlp-corpora/doc

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

- [ ] Clean up existing entries

- [ ] Overall usage

    - [ ] Pie chart showing overall usage breakdown

    - [ ] Fail overall check (+ email) if usage gets above threshold (e.g., 95%)

- [ ] Check if staging grounds empty

- [ ] Migrate this to `uwnlp` github

- [ ] Send announcement
