# nlp-corpora-backend

This repository contains the infrastructure to provide a live status of
`/projects/nlp-corpora/` by crawling its contents.

## Features

Checks over contents of all corpora (sub)directories.

Per-corpus:

- owner
- group
- permissions
- configurable access restrictions (groups and permissions)
- corpus structure adherence
- readme existence
- readme project description
- readme documentation (of processed variants)
- size

Overall:

- can fix permissions errors automatically with a flag
- total size checks (above a configurable drive limit)
- log containing detailed status breakdown and all errors
- report generation
    - copies readme into browsable index
    - concise summary per corpus (name, readme link, description, size, access, status)
- pie chart of overall size usage
- configured cron usage:
    - self-updates backend and runs daily
    - pushes updated report to frontend
    - emails full error log on failures (configurable verbosity)

## Installation

```bash
# create a fresh virtualenv. I use pyenv. You can use whatever.
# Use python >= 3.6.5. Then:
pip install -r requirements.txt
```

## Running

```bash
# also prints log to stderr if any checks failed. (This behavior so cron
# auto sends an email to you if anything fails, but not if things pass.)
python check.py \
    --directory /projects/nlp-corpora/ \
    --out-file ~/repos/nlp-corpora/README.md \
    --log-file ~/repos/nlp-corpora/BUILD.txt \
    --doc-dir ~/repos/nlp-corpora/doc \
    --plot-dest ~/repos/nlp-corpora/disk-usage.svg

# The script can attempt to fix permission errors it finds. This isn't normally
# run in the cron job (though it could be). It can be enabled with a flag:
python check.py --fix-perms

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

- [ ] Check whether `_staging` and `nobackup` empty

- [ ] Migrate this to `uwnlp` github

- [ ] Send announcement
