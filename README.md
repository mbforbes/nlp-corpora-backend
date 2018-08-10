# nlp-corpora-backend

This repository contains the infrastructure to provide a live status of
`/projects/nlp-corpora/` by crawling its contents.

## Features

Checks over contents of all corpora (sub)directories.

Per-corpus:

- [x] owner
- [x] group
- [x] permissions
- [x] configurable access restrictions (groups and permissions)
- [x] corpus structure adherence
- [x] readme existence
- [x] readme project description
- [x] readme documentation (of processed variants)
- [x] size

Overall:

- [x] can fix permissions errors automatically with a flag
- [x] total size checks (above a configurable drive limit)
- [x] log containing detailed status breakdown and all errors
- [x] report generation
    - [x] copies readme into browsable index
    - [x] concise summary per corpus (name, readme link, description, size, access, status)
    - [x] pie chart of overall size usage
- [x] configured cron usage:
    - [x] self-updates backend and runs daily
    - [x] pushes updated report to frontend
    - [x] emails full error log on failures (configurable verbosity)

## Installation

```bash
# create a fresh virtualenv. I use pyenv. You can use whatever.
# Use python >= 3.6.5. Then:
pip install -r requirements.txt
```

## Running

Example usage:

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

Full options:

```
python check.py --help
usage: check.py [-h] [--directory DIRECTORY] [--ok-owners OK_OWNERS]
                [--group-config GROUP_CONFIG] [--fix-perms] [--verbose]
                [--out-file OUT_FILE] [--log-file LOG_FILE]
                [--doc-dir DOC_DIR] [--plot-dest PLOT_DEST]

Tool to check nlp-corpora directory and output documentation.

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY
                        path to top-level corpus directory (default:
                        /projects/nlp-corpora/)
  --ok-owners OK_OWNERS
                        comma-separated list of allowed owners (default:
                        mbforbes)
  --group-config GROUP_CONFIG
                        json file containing group information (default:
                        groups.json)
  --fix-perms           whether this should attempt to fix permission errors
                        it finds (default: False)
  --verbose             whether to log error messages for every problematic
                        file (default: False)
  --out-file OUT_FILE   path to write output file. If not provided, writes to
                        stdout. (default: None)
  --log-file LOG_FILE   if provided, writes log to this path. If not 100% of
                        checks pass, always writes log to stderr. (default:
                        None)
  --doc-dir DOC_DIR     if provided, DESTROYS this dir if it exists, creates
                        it fresh, and then writes directories and readmes for
                        all corpora under it. (default: None)
  --plot-dest PLOT_DEST
                        if provided, writes a donut plot of corpora disk space
                        usage to this location. (default: None)
```
