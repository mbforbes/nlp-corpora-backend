"""
Checker script to crawl /projects/nlp-corpora/ directory.
"""

#
# imports
#

# builtins
import argparse
import code
import glob
import os
import subprocess
import sys
from typing import Any, List, Optional

# 3rd party
from mypy_extensions import TypedDict


#
# globals
#

class DirResult(TypedDict):
    """information we want from all results"""
    basename: str
    description: Optional[str]
    size: str
    dir_clean: bool
    readme_exists: bool
    readme_complete: bool


# These are the things allowed to be in the top-level directory that aren't
# checked.
BLACKLIST = [
    'nobackup',
    '_staging',  # TODO(mbforbes): Special check in here.
]

# These are the only things allowed in a top-level (corpus) directory.
CLEAN_DIR_WHITELIST = [
    'original',
    'processed',
    'README.md',
]

# file to use as header for results
HEADER_FN = 'header.md'

# file to use as footer for results
FOOTER_FN = 'footer.md'


#
# functions
#

def get_size(path: str) -> str:
    """
    Thanks to https://stackoverflow.com/a/25574638
    """
    return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')


def get_dirs(base_dir: str) -> List[str]:
    # get all subdirectories
    globs = glob.glob(os.path.join(base_dir, '*'))
    paths = []
    for path in globs:
        if os.path.basename(path) not in BLACKLIST:
            paths.append(path)
    return paths


def check_dir(path: str) -> DirResult:
    """
    For a corpus directory (`path`), checks its properties to ensure they
    conform to the nlp-corpora guidelines.

    Calling this `path` and not `directory` or something because it may
    actually end up being a file and not a directory, and we need to handle
    that case. Also, it's a full path, not just a local directory.
    """
    # define res upfront and mutate as we discover things
    res: DirResult = {
        'basename': os.path.basename(path),
        'description': None,
        'size': get_size(path),
        'dir_clean': False,
        'readme_exists': False,
        'readme_complete': False,
    }

    # edge case: if it's a file instead of a directory, everything else should
    # be marked as invalid and should just return now.
    if not os.path.isdir(path):
        return res

    # The rest of the options don't depend on whether the directory is clean,
    # so we just check that first.
    res['dir_clean'] = True
    for inner in glob.glob(os.path.join(path, '*')):
        if os.path.basename(inner) not in CLEAN_DIR_WHITELIST:
            res['dir_clean'] = False
            break

    # Check whether readme even exists. If it doesn't it can't be complete and
    # can't have a description, so we just stop checking now and return.
    readme_fn = os.path.join(path, 'README.md')
    if not os.path.isfile(readme_fn):
        return res
    res['readme_exists'] = True

    # README.md format:
    #
    # ```
    # # <title>
    # <description>
    #
    # <rest of contents>
    # ```

    # Read in entire readme.
    with open(readme_fn, 'r') as f:
        readme = [line.strip() for line in f.readlines()]

    # Description is second non-empty line in readme (first is title).
    for line in readme[1:]:
        if len(line) > 0:
            res['description'] = line
            break

    # Pre-check: if no "processed" directories exist, the README doesn't need
    # to talk about them.
    res['readme_complete'] = True
    processed_dir = os.path.join(path, 'processed')
    if not os.path.isdir(processed_dir):
        return res

    # Processed directories exist. Make sure the readme talks about all of
    # them.
    full_readme = ' '.join(readme)
    for p_subdir in glob.glob(os.path.join(processed_dir, '*')):
        if os.path.basename(p_subdir) not in full_readme:
            res['readme_complete'] = False
            break

    return res


def debug_print_results(results: List[DirResult]) -> None:
    fmt = '{} \t {} \t {} \t {} \t {} \t {}'
    print(fmt.format(
        'dirname', 'desc', 'size', 'dir clean', 'README exists',
        'README complete'))
    for res in results:
        print(fmt.format(
            res['basename'], res['description'], res['size'], res['dir_clean'],
            res['readme_exists'], res['readme_complete']))


def fun_bool(boring: bool) -> str:
    return '✔' if boring else '✗'


def generate_results_markdown(results: List[DirResult]) -> str:
    fmt = '{} | {} | {} | {} | {} | {}'
    header = fmt.format('dirname', 'desc', 'size', 'dir clean',
        'README exists', 'README complete')
    separator = fmt.format('---', '---', '---', '---', '---', '---')
    rows = []
    for res in results:
        rows.append(fmt.format(
            res['basename'], res['description'], res['size'],
            fun_bool(res['dir_clean']),
            fun_bool(res['readme_exists']),
            fun_bool(res['readme_complete'])
        ))
    return '\n'.join([header, separator] + rows)


def compute_success(results: List[DirResult]) -> bool:
    """Returns whether we had 100% passing checks."""
    for r in results:
        if not (r['dir_clean'] and r['readme_exists'] and r['readme_complete']):
            return False
    return True


def generate_log(success: bool, results: List[DirResult]) -> str:
    """Takes results and generates log file for more detailed results."""
    return '\n'.join([
        'Overall pass: {}'.format(success),
        '',
        'Log not yet implemented',
    ])


def check(base_dir: str) -> List[DirResult]:
    paths = get_dirs(base_dir)
    return [check_dir(p) for p in paths]


def main() -> None:
    # cmd line args
    parser = argparse.ArgumentParser(
        description='Tool to check nlp-corpora directory and output documentation.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='/projects/nlp-corpora/',
        help='path to top-level corpus directory')
    parser.add_argument(
        '--out-file',
        type=str,
        help='path to write output file. If not provided, writes to stdout.')
    parser.add_argument(
        '--log-file',
        type=str,
        help='if provided, writes log to this path. If not 100%% of checks pass, always writes log to stderr.')
    args = parser.parse_args()

    with open(HEADER_FN, 'r') as f:
        header = f.read()
    with open(FOOTER_FN, 'r') as f:
        footer = f.read()

    results = check(args.directory)
    success = compute_success(results)

    out_md = generate_results_markdown(results)
    out = '\n'.join([header, out_md, footer])

    # output
    if args.out_file is not None:
        with open(os.path.expanduser(args.out_file), 'w') as f:
            f.write(out)
    else:
        print(out)

    # log. always write to log file, if provided. write to stderr only if the
    # overall results was not 100% successful.
    log = generate_log(success, results)
    if args.log_file is not None:
        with open(os.path.expanduser(args.log_file), 'w') as f:
            f.write(log)
    if not success:
        print(log, file=sys.stderr)


if __name__ == '__main__':
    main()
