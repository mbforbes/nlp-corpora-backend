"""
Checker script to crawl /projects/nlp-corpora/ directory.
"""

#
# imports
#

# builtins
import argparse
import code
import datetime
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
    readme_desc: bool
    readme_proc_desc: bool


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

BADGE_RESULT_FMT = '![](https://img.shields.io/badge/docs-{success}-{color}.svg?longCache=true&style=flat)'
BADGE_DATE_FMT = '![](https://img.shields.io/badge/built-{date}-blue.svg?longCache=true&style=flat)'

#
# functions
#

def read(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def build_top(success: bool) -> str:
    """Returns the markdown title and badges. Should go above header in output
    file."""
    badge_result = BADGE_RESULT_FMT.format(
        success=('passing' if success else 'errors'),
        color=('brightgreen' if success else 'red'),
    )
    badge_date = BADGE_DATE_FMT.format(date='{:%-m/%-d/%y}'.format(datetime.datetime.now()))
    return '\n'.join([
        '# nlp-corpora',
        '',
        badge_result,
        badge_date,
        '',
    ])


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
    return sorted(paths)


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
        'readme_desc': False,
        'readme_proc_desc': False,
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

    # Must have something in desc to pass desc-having check.
    res['readme_desc'] = res['description'] is not None

    # Pre-check: if no "processed" directories exist, the README doesn't need
    # to talk about them.
    res['readme_proc_desc'] = True
    processed_dir = os.path.join(path, 'processed')
    if not os.path.isdir(processed_dir):
        return res

    # Processed directories exist. Make sure the readme talks about all of
    # them.
    full_readme = ' '.join(readme)
    for p_subdir in glob.glob(os.path.join(processed_dir, '*')):
        if os.path.basename(p_subdir) not in full_readme:
            res['readme_proc_desc'] = False
            break

    return res


def fun_bool(boring: bool) -> str:
    return '✔' if boring else '✗'


def generate_results_markdown(results: List[DirResult]) -> str:
    fmt = '{} | {} | {} | {}'
    header = fmt.format('dirname', 'desc', 'size', 'status')
    separator = fmt.format(*(['---']*4))
    rows = []
    for res in results:
        rows.append(fmt.format(
            res['basename'],
            res['description'],
            res['size'],
            fun_bool(compute_result_success(res)),
        ))
    return '\n'.join([header, separator] + rows)


def compute_result_success(r: DirResult) -> bool:
    return r['dir_clean'] and r['readme_exists'] and r['readme_desc'] and r['readme_proc_desc']


def compute_success(results: List[DirResult]) -> bool:
    """Returns whether we had 100% passing checks."""
    for r in results:
        if not compute_result_success(r):
            return False
    return True


def generate_log(success: bool, results: List[DirResult]) -> str:
    """Takes results and generates log file for more detailed results."""
    buffer = ['Overall pass: {}'.format(success), '']
    fmt = '{!s:20.19} {!s:20.19} {!s:10.9} {!s:10.9} {!s:8.7} {!s:7.6} {!s:7.6}'
    header = ('dirname', 'desc', 'size', 'dir clean', 'README?', 'R-desc', 'R-proc')

    buffer.append(fmt.format(*header))
    buffer.append(fmt.format(*(['---'] * 7)))
    for res in results:
        buffer.append(fmt.format(
            res['basename'],
            res['description'],
            res['size'],
            fun_bool(res['dir_clean']),
            fun_bool(res['readme_exists']),
            fun_bool(res['readme_desc']),
            fun_bool(res['readme_proc_desc']),
        ))

    return '\n'.join(buffer)


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

    # run
    results = check(args.directory)
    success = compute_success(results)

    # build out md file
    out = '\n'.join([
        build_top(success),
        read(HEADER_FN),
        generate_results_markdown(results),
        read(FOOTER_FN),
    ])

    # write output
    if args.out_file is not None:
        with open(os.path.expanduser(args.out_file), 'w') as f:
            f.write(out)
    else:
        print(out)

    # write log. always write to log file, if provided. write to stderr only if
    # the overall results was not 100% successful.
    log = generate_log(success, results)
    if args.log_file is not None:
        with open(os.path.expanduser(args.log_file), 'w') as f:
            f.write(log)
    if not success:
        print(log, file=sys.stderr)


if __name__ == '__main__':
    main()
