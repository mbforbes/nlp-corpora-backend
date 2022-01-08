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
import grp
import json
import os
import platform
import pwd
import shutil
import stat
import subprocess
import sys
from typing import Any, List, Optional, Set, Tuple, Dict

# 3rd party
import humanfriendly
import matplotlib
matplotlib.use('Agg')  # set backed to avoid crash on non X-window server
import matplotlib.pyplot as plt
from mypy_extensions import TypedDict


#
# globals
#

class DirResult(TypedDict):
    """information we want from all results"""
    basename: str
    description: Optional[str]
    size_raw: int
    size_human: Optional[str]
    group_ok: bool
    group: Optional[str]
    owner_ok: bool
    perms_ok: bool
    dir_clean: bool
    readme_exists: bool
    readme_path: Optional[str]
    readme_desc: bool
    readme_proc_desc: bool
    errors: List[str]


class RestrictedGroup(TypedDict):
    """Information about a restricted group (provided in json file)."""
    desc: str


class Permissions(TypedDict):
    """A set of permissions to use for a single corpus directory."""
    # top = the named corpus directory
    top: int
    # readme = README.md
    readme: int
    # contents = original/, processed/, and any subfolders/files
    contents_dir: int
    contents_file: int

# r--r--r--
PERM_ALL_R = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH

# r-xr-xr-x
PERM_ALL_RX = PERM_ALL_R | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

# r--r-----
PERM_UG_R = stat.S_IRUSR | stat.S_IRGRP

# r-xr-x---
PERM_UG_RX = PERM_UG_R | stat.S_IXUSR | stat.S_IXGRP

STD_PERMS: Permissions = {
    'top': PERM_ALL_RX,
    'readme': PERM_ALL_R,
    'contents_dir': PERM_ALL_RX,
    'contents_file': PERM_ALL_R,
}

RESTRICTED_PERMS: Permissions = {
    'top': PERM_ALL_RX,
    'readme': PERM_ALL_R,
    'contents_dir': PERM_UG_RX,
    'contents_file': PERM_UG_R,
}

# These are the things allowed to be in the top-level directory that aren't
# checked for corpora, but should be empty.
WHITELIST_DIRS = [
    'nobackup',
    '_staging',
]

# These are files we're ok with existing in the root of the repository.
WHITELIST_FILES = [
    'README.md',
]

# These are the only things allowed in a top-level (corpus) directory.
CLEAN_DIR_WHITELIST = [
    'original',
    'processed',
    'README.md',
]

# amount above which we worry available space is running low
TOTAL_SIZE_WORRY = 1400000000000  # ~= 1.4 TB

# files containing pre-written fixed markdown content we copy into the output
# readme.
HEADER_FN = 'header.md'
MID_FN = 'mid.md'
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


def get_size(path: str) -> int:
    """
    Returns size in bytes.
    """
    # Thanks to https://stackoverflow.com/a/25574638. Additional note: we
    # switch based on platform because BSD doesn't support the -b option.
    # (Better implementation would be to do in python.)
    plat = platform.system()
    if plat == 'Linux':
        return int(subprocess.check_output(['du','-bs', path]).split()[0].decode('utf-8'))
    elif plat == 'Darwin':
        return 512 * int(subprocess.check_output(['du','-s', path]).split()[0].decode('utf-8'))
    else:
        raise ValueError('Unimplemented platform: "{}"'.format(plat))


def get_dirs(base_dir: str) -> List[str]:
    whitelist = WHITELIST_DIRS + WHITELIST_FILES
    # get all subdirectories
    globs = glob.glob(os.path.join(base_dir, '*'))
    paths = []
    for path in globs:
        if os.path.basename(path) not in whitelist:
            paths.append(path)
    return sorted(paths)


def extract_group_config(path: str) -> Tuple[Set[str], Dict[str, RestrictedGroup]]:
    """Returns (std_grps, restricted_grps)"""
    config = json.loads(read(path))
    return (set(config['standard']), config['restricted'])


def get_grp(path: str) -> str:
    return grp.getgrgid(os.stat(path).st_gid).gr_name


def check_grp(path: str, want_grp: str) -> Tuple[bool, List[str]]:
    """Returns whether it passed, and any errors."""
    actual_grp = get_grp(path)
    if want_grp != actual_grp:
        return False, ['Expected "{}" to have group "{}", but had group "{}"'.format(
            path, want_grp, actual_grp,
        )]
    return True, []


def get_perms(
        path: str,
        std_grps: Set[str],
        restrict_grps: Dict[str, RestrictedGroup],
    ) -> Tuple[Permissions, str, List[str]]:
    """Returns (permissions to use, group name, list of error messages)"""
    grp_name = get_grp(path)
    if grp_name in std_grps:
        return STD_PERMS, grp_name, []
    elif grp_name in restrict_grps:
        return RESTRICTED_PERMS, grp_name, []
    else:
        all_grps = ', '.join(list(std_grps) + list(restrict_grps.keys()))
        return (
            RESTRICTED_PERMS,
            grp_name,
            ['Unknown group "{}"; known groups: "{}"'.format(grp_name, all_grps)],
        )


def check_op(
        path: str,
        ok_owners: Set[str],
        want_perms: int,
        change: bool = False,
    ) -> Tuple[bool, bool, List[str]]:
    """Check owner and permissions (and maybe change them)."""
    owner_passed = True
    perms_passed = True
    errors: List[str] = []

    s = os.stat(path)

    # check owner
    owner = pwd.getpwuid(s.st_uid).pw_name
    if owner not in ok_owners:
        owner_passed = False
        errors.append('Path "{}" has owner "{}", but needs to be one of "{}"'.format(
            path, owner, ok_owners,
        ))

    # pre-check whether script could change permissions if asked to.
    can_change = os.getuid() == s.st_uid

    # check permissions
    cur_perms = stat.S_IMODE(s.st_mode)
    if cur_perms != want_perms:
        # failed; maybe change
        if change and can_change:
            os.chmod(path, want_perms)
        else:
            perms_passed = False
            errors.append('Path "{}" has mode "{}", but want mode to be "{}"'.format(
                path, cur_perms, want_perms,
            ))

    return (owner_passed, perms_passed, errors)


def check_gop(
        res: DirResult,
        path: str,
        want_grp: str,
        ok_owners: Set[str],
        want_perms: int,
        change: bool = False,
        extend_errors: bool = True,
    ) -> Tuple[bool, bool, bool]:
    """Wrapper to help in checking group, owner, and perms, and merge results
    into current results.

    extend_errors --- provided to avoid GB of logs when all files are wrong LOL
    """
    # grp
    grp_ok, grp_errors = check_grp(path, want_grp)
    res['group_ok'] = res['group_ok'] and grp_ok
    if extend_errors:
        res['errors'].extend(grp_errors)

    # owner + perms
    owner_ok, perms_ok, op_errors = check_op(path, ok_owners, want_perms, change)
    res['owner_ok'] = res['owner_ok'] and owner_ok
    res['perms_ok'] = res['perms_ok'] and perms_ok
    if extend_errors:
        res['errors'].extend(op_errors)

    return grp_ok, owner_ok, perms_ok


def walk_check(
        res: DirResult,
        root: str,
        want_grp: str,
        ok_owners: Set[str],
        want_dir_perms: int,
        want_file_perms: int,
        change: bool = False,
        verbose: bool = False,
    ) -> None:
    """Checks group / owner / perms recursively under a directory (e.g.,
    'original/' or 'processed/')."""
    g, o, p = True, True, True
    for dirpath, dirnames, filenames in os.walk(root):
        rg, ro, rp = check_gop(res, dirpath, want_grp, ok_owners, want_dir_perms, change, verbose)
        g, o, p = g and rg, o and ro, p and rp
        for filename in filenames:
            rg, ro, rp = check_gop(res, os.path.join(dirpath, filename), want_grp, ok_owners, want_file_perms, change, verbose)
            g, o, p = g and rg, o and ro, p and rp

    # if not verbose, we didn't add individual error messages, so add some now
    if not verbose:
        base_msg = 'One or more file/dirs at/below "{}" has {} errors.'
        if not g:
            res['errors'].append(base_msg.format(root, 'group'))
        if not o:
            res['errors'].append(base_msg.format(root, 'owner'))
        if not p:
            res['errors'].append(base_msg.format(root, 'permission'))



def check_dir(
        path: str,
        std_grps: Set[str],
        restricted_grps: Dict[str, RestrictedGroup],
        ok_owners: Set[str],
        fix_perms: bool = False,
        verbose: bool = False,
    ) -> DirResult:
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
        'size_raw': 0,
        'size_human': None,
        'group_ok': True,
        'group': None,
        'owner_ok': True,
        'perms_ok': True,
        'dir_clean': False,
        'readme_exists': False,
        'readme_path': None,
        'readme_desc': False,
        'readme_proc_desc': False,
        'errors': [],
    }

    size_bytes = get_size(path)
    res['size_raw'] = size_bytes
    res['size_human'] = humanfriendly.format_size(size_bytes)

    # edge case: if it's a file instead of a directory, everything else should
    # be marked as invalid and should just return now.
    if not os.path.isdir(path):
        res['errors'].append('Not a directory but in top-level.')
        return res

    # get set of permissions. if the group isn't known, we don't know the right
    # permissions to use and we probably don't want everything below it to have
    # the same (wrong) group, so we stop early.
    perms, grp_name, grp_errors = get_perms(path, std_grps, restricted_grps)
    if len(grp_errors) > 0:
        res['group_ok'] = False
        res['errors'].extend(grp_errors)
        return res
    res['group'] = grp_name

    # check group + owner + perms of directory itself
    check_gop(res, path, grp_name, ok_owners, perms['top'], fix_perms)

    # The rest of the options don't depend on whether the directory is clean,
    # so we just check that first.
    res['dir_clean'] = True
    for inner in glob.glob(os.path.join(path, '*')):
        inner_basename = os.path.basename(inner)
        if inner_basename not in CLEAN_DIR_WHITELIST:
            res['dir_clean'] = False
            res['errors'].append('Directory not clean: bad entry: "{}".'.format(inner_basename))

    # Check whether readme even exists. If it doesn't it can't be complete and
    # can't have a description, so we just stop checking now and return.
    readme_fn = os.path.join(path, 'README.md')
    if not os.path.isfile(readme_fn):
        res['errors'].append('Missing README.md')
        return res
    res['readme_exists'] = True
    res['readme_path'] = readme_fn

    # check readme group, owner, perms
    check_gop(res, readme_fn, grp_name, ok_owners, perms['readme'], fix_perms)

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
    if not res['readme_desc']:
        res['errors'].append('Missing description (second non-empty line) in README.md')

    # Check original/ directory recursively for group/owner/perms.
    walk_check(
        res,
        os.path.join(path, 'original'),
        grp_name,
        ok_owners,
        perms['contents_dir'],
        perms['contents_file'],
        fix_perms,
        verbose,
    )

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
        p_subdir_basename = os.path.basename(p_subdir)
        if p_subdir_basename not in full_readme:
            res['readme_proc_desc'] = False
            res['errors'].append('Missing description in README.md for processed variant: "{}"'.format(
                p_subdir_basename
            ))

    # Check processed/ directory recursively for group/owner/perms.
    walk_check(
        res,
        processed_dir,
        grp_name,
        ok_owners,
        perms['contents_dir'],
        perms['contents_file'],
        fix_perms,
        verbose,
    )

    return res


def fun_bool(boring: bool) -> str:
    return '✓' if boring else '✗'


def generate_results_markdown(results: List[DirResult], std_grps: Set[str]) -> str:
    """Generates table for README.md giving corpora status overview."""
    fmt = '{} | {} | {} | {} | {}'
    header = fmt.format('Corpus', 'Description', 'Size', '[Access](#restricted-access)', 'Status')
    separator = fmt.format(*(['---']*5))
    rows = []
    for res in results:
        rows.append(fmt.format(
            '[{}]({})'.format(res['basename'], os.path.join('doc/', res['basename'])),
            res['description'],
            res['size_human'],
            fun_bool(True) if res['group'] in std_grps else '[`{}`](#restricted-access)'.format(res['group']),
            fun_bool(compute_result_success(res)),
        ))
    return '\n'.join([header, separator] + rows)


def generate_access_markdown(restricted_grps: Dict[str, RestrictedGroup]) -> str:
    """Generates table for README.md describing how to access restricted corpora."""
    fmt = '{} | {}'
    header = fmt.format('Access', 'How to be added')
    sep = fmt.format(*(['---']*2))
    rows = []
    for name, grpinfo in restricted_grps.items():
        rows.append(fmt.format(
            '`{}`'.format(name),
            grpinfo['desc'],
        ))
    return '\n'.join([header, sep] + rows)


def compute_result_success(r: DirResult) -> bool:
    return (
        r['group_ok'] and r['owner_ok'] and r['perms_ok'] and
        r['dir_clean'] and r['readme_exists'] and r['readme_desc'] and
        r['readme_proc_desc']
    )


def compute_success(results: List[DirResult]) -> bool:
    """Returns whether we had 100% passing checks."""
    for r in results:
        if not compute_result_success(r):
            return False
    return True


def build_doc_dir(results: List[DirResult], doc_dir: str) -> None:
    # clean doc dir to remove anything that exists, then create it fresh
    if os.path.exists(doc_dir):
        if os.path.isdir(doc_dir):
            shutil.rmtree(doc_dir)
        else:
            os.remove(doc_dir)
    os.makedirs(doc_dir)

    for res in results:
        # make the dir
        corpus_dir = os.path.join(doc_dir, res['basename'])
        os.makedirs(corpus_dir)

        # either copy real readme, or write a tmp dummy one
        readme_fn = os.path.join(corpus_dir, 'README.md')
        if res['readme_exists'] and res['readme_path'] is not None:
            shutil.copy(res['readme_path'], readme_fn)
        else:
            with open(readme_fn, 'w') as f:
                f.write('# {}\n\n(readme is missing! add one soon!)\n'.format(
                    res['basename'],
                ))


def plot(results: List[DirResult], plot_dest: str) -> None:
    """Writes donut plot of disk usages to plot_dest."""
    total_size = sum([r['size_raw'] for r in results])
    group_sizes = [r['size_raw']/total_size for r in results]
    group_names = [
        '{}\n({})'.format(r['basename'], r['size_human'])
        if r['size_raw']/total_size > .03 else ''
        for r in results
    ]

    # Create colors
    #a, b, c=[plt.cm.Blues, plt.cm.Reds, plt.cm.Greens]

    # Plot
    fig, ax = plt.subplots()
    ax.axis('equal')
    mypie, _ = ax.pie(group_sizes, radius=0.8, labels=group_names, )#colors=[a(0.6), b(0.6), c(0.6)] )
    plt.setp(mypie, width=0.7, edgecolor='white')

    # Save
    plt.savefig(plot_dest)


def generate_log(base_dir: str, success: bool, results: List[DirResult]) -> str:
    """Takes results and generates log file for more detailed results."""
    # overall
    buffer = ['Overall pass: {}'.format(success), '']

    # summary table
    fmt = '{!s:20.19} {!s:20.19} {!s:10.9} {!s:6.5} {!s:6.5} {!s:6.5} {!s:10.9} {!s:8.7} {!s:7.6} {!s:7.6}'
    header = ('dirname', 'desc', 'size', 'group', 'owner', 'perms', 'dir clean', 'README?', 'R-desc', 'R-proc')
    buffer.append(fmt.format(*header))
    buffer.append(fmt.format(*(['---'] * 10)))
    for res in results:
        buffer.append(fmt.format(
            res['basename'],
            res['description'],
            res['size_human'],
            fun_bool(res['group_ok']),
            fun_bool(res['owner_ok']),
            fun_bool(res['perms_ok']),
            fun_bool(res['dir_clean']),
            fun_bool(res['readme_exists']),
            fun_bool(res['readme_desc']),
            fun_bool(res['readme_proc_desc']),
        ))
    buffer.append('')

    # detailed errors per result
    if not success:
        buffer.append('Detailed errors:')
        for res in results:
            if len(res['errors']) > 0:
                buffer.append(res['basename'])
                buffer.append('-'*80)
                for e in res['errors']:
                    buffer.append(' - {}'.format(e))
                buffer.append('')

    # total size check
    total_used = sum([r['size_raw'] for r in results])
    if total_used >= TOTAL_SIZE_WORRY:
        buffer.append('Total bytes used ({}) above worry limit ({})'.format(
            humanfriendly.format_size(total_used),
            humanfriendly.format_size(TOTAL_SIZE_WORRY),
        ))
        buffer.append('May need to look into expanding disk size soon!')

    # whitelist dirs empty check
    for b in WHITELIST_DIRS:
        d = os.path.join(base_dir, b)
        n_contents = len(os.listdir(d)) if os.path.isdir(d) else 0
        if n_contents > 0:
            buffer.append('Wanted directory "{}" to be empty, but contained {} files.'.format(
                d, n_contents,
            ))

    return '\n'.join(buffer)


def check(
        base_dir: str,
        std_grps: Set[str],
        restricted_grps: Dict[str, RestrictedGroup],
        ok_owners: Set[str],
        fix_perms: bool = False,
        verbose: bool = False,
    ) -> List[DirResult]:
    paths = get_dirs(base_dir)
    return [
        check_dir(p, std_grps, restricted_grps, ok_owners, fix_perms, verbose)
        for p in paths
    ]


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
        '--ok-owners',
        type=str,
        default='sg01',
        help='comma-separated list of allowed owners')
    parser.add_argument(
        '--group-config',
        type=str,
        default='groups.json',
        help='json file containing group information')
    parser.add_argument(
        '--fix-perms',
        action='store_true',
        help='whether this should attempt to fix permission errors it finds')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='whether to log error messages for every problematic file')
    parser.add_argument(
        '--out-file',
        type=str,
        help='path to write output file. If not provided, writes to stdout.')
    parser.add_argument(
        '--log-file',
        type=str,
        help='if provided, writes log to this path. If not 100%% of checks pass, always writes log to stderr.')
    parser.add_argument(
        '--doc-dir',
        type=str,
        help='if provided, DESTROYS this dir if it exists, creates it fresh, and then writes directories and readmes for all corpora under it.')
    parser.add_argument(
        '--plot-dest',
        type=str,
        help='if provided, writes a donut plot of corpora disk space usage to this location.')
    args = parser.parse_args()

    # extract
    std_grps, restricted_grps = extract_group_config(args.group_config)
    ok_owners = set(args.ok_owners.split(','))

    # run
    results = check(args.directory, std_grps, restricted_grps, ok_owners, args.fix_perms, args.verbose)
    success = compute_success(results)

    # build out md file
    out = '\n'.join([
        build_top(success),
        read(HEADER_FN),
        generate_results_markdown(results, std_grps),
        read(MID_FN),
        generate_access_markdown(restricted_grps),
        read(FOOTER_FN),
    ])

    # write output
    if args.out_file is not None:
        with open(os.path.expanduser(args.out_file), 'w') as f:
            f.write(out)
    else:
        print(out)

    # maybe write doc dir
    if args.doc_dir is not None:
        build_doc_dir(results, os.path.expanduser(args.doc_dir))

    # maybe write plot
    if args.plot_dest is not None:
        plot(results, os.path.expanduser(args.plot_dest))

    # write log. always write to log file, if provided. write to stderr only if
    # the overall results was not 100% successful.
    log = generate_log(args.directory, success, results)
    if args.log_file is not None:
        with open(os.path.expanduser(args.log_file), 'w') as f:
            f.write(log)
    if not success:
        print(log, file=sys.stderr)


if __name__ == '__main__':
    main()
