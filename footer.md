

### Access outside UW CSE

Accessing the corpora requires a UW CSE unix account. Anyone can receive a free
UW CSE guest account by having a UW CSE faculty or staff [sponsor
them](https://sponsor.cs.washington.edu/). Despite the name "sponsor," this is
absolutely _free_ for both parties. Guest accounts last up to two years and can
be renewed indefinitely. This is the way to grant NLP friends in EE and
linguistics access to nlp-corpora.


## Corpus structure

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



## Bugs / questions / contributions

For any bugs or questions, please open a GitHub issue on this repository (top
of the webpage).

To help contribute to this project, please check out the [backend
repository](https://github.com/mbforbes/nlp-corpora-backend) and open issues or
pull requests there.
