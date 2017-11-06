
### Legend

key | meaning
--- | ---
dirname | The name of the top-level corpus directory within `nlp-corpora`
desc | The description found in the README.md file for the corpus
size | The total size of the corpus directory
dir clean | Whether only the allowed directories and files were found
README exists | Whether the `README.md` file was found
README complete | Whether the `README.md` file contained descriptions for all subdirectories in `processed/`

## Documentation

Inside the `/projects/nlp-corpora/` directory, there should only be directories
for corpora.

Each corpus directory `<name>` should have the following format:

```
<name>
├── original/
│   └── ...
├── processed/
│   └── ...
└── README.md
```

No other top-level contents in the corpus directory is allowed.

Each of the components should be as follows:

### `original/`

_Optional_

The `original/` subdirectory should contain the source material in the most
raw, unprocessed form possible. If the source material was downloaded as a
tarball, it should be that tarball. If it was downloaded as a set of files
comprising a dataset, it should be those files. If it was scraped from a
website, it should be the raw output of the scraping command (e.g., `curl` or
`wget`).

This may not exist for all corpora, but it is preferred to exist if possible.

### `processed/`

_Optional_

The `processed/` subdirectory should contain only subdirectories, no files.
Each subdirectory should be a succinct name for the type of processing that its
contents underwent. For example, if many text files were cleaned and joined
into one, `txt`, would be an appropriate name. If tokenization was applied,
`tkn` would be an appropriate name.

Details for all subdirectories within `processed/` must be provided in the
`README.md` file (more information on this below).

### `README.md`

_Required_

The `README.md` file is required because it provides all documentation about
the data source.

In general, it should have the following format:

```
# (tile of the corpus)

(Short description of the corpus.)

(How the corpus was acquired (including the URL or the contents of the script).)

(When the corpus was acquired.)

(For each subdirectory in "processed/" (if any exist), a description of how
that directory was created. Optimal is a script (or a link to a specific
version of a script). Also acceptable is an English description. For example,
if it was tokenized, which tokenizer was used, and which version of that
software.)
```

## Contributing

Current feature worklist:

- [ ] Resolve python3.4/3.6 usage on some dept. server and settle on type usage
- [ ] Actually run on (some) dept server w/ cron job (add monthly reminder to
      ensure actually running)
- [ ] Owner checks (TODO: should only be admins?)
- [ ] Permissions checks (TODO: )
- [ ] Process to request new directories + followup (probably form + linked on
      README?)
- [ ] Hashing for `original/`
- [ ] Copy corpus directories' `README.md`s into here (under corpus names) and
  link on status table so that all docs can be browsed from this master
  README.md
- [ ] Badge showing how recently checker job was run
- [ ] Automatically discover username to blame for directory failing any checks
- [ ] Email blamed users (and admin) at fixed interval
- [ ] Pie chart showing overall usage breakdown
- [ ] Email admin if usage gets above threshold (e.g., 90%)
- [ ] Generate log of passed / failed check html page w/ headers; link failures
      from status to log
- [ ] If possible, color code the check / cross marks
- [ ] Make all existing dirs conform to standards; migrate tmp model dirs
- [ ] `uwnlp` github org w/ private repos
- [ ] Migrate this to `uwnlp` github
- [ ] Have 1-2 others (both in and outside nlp-corpora group) beta test the
      process to work out snags
- [ ] Send announcement
