import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from os import PathLike
from pathlib import Path
from typing import List, Optional, Union

import click

from stramp.configfile import get_config
from stramp.docstruct import DocFile
from stramp.globalstate import get_global_state
from stramp.hashing import hash_files
from stramp.paths import paths

re_hash_file_name = re.compile(r'hashes-\d{14}\.json')


def create_directories() -> None:
    paths.app_dir_path.mkdir(exist_ok=True)
    paths.data_dir_path.mkdir(exist_ok=True)
    paths.new_dir_path.mkdir(exist_ok=True)
    paths.stamped_dir_path.mkdir(exist_ok=True)
    paths.complete_dir_path.mkdir(exist_ok=True)


def hash_document(file_name: str) -> DocFile:

    quoted_file_name = quote_path(file_name)
    copy_path = paths.data_dir_path / quoted_file_name  # type: Union[PathLike, Path]
    shutil.copy2(file_name, copy_path)

    file_hash = hashlib.sha256(copy_path.read_bytes()).hexdigest()[:16]
    quoted_file_name_with_hash = quoted_file_name + '#' + file_hash
    copy_with_hash_path = paths.data_dir_path / quoted_file_name_with_hash  # type: Union[PathLike, Path]
    os.rename(copy_path, copy_with_hash_path)

    return DocFile(Path(file_name), file_data_path=copy_with_hash_path)


def hash_documents() -> Path:

    config = get_config()

    documents = config.get('documents')  # type: List[str]

    org_documents = []
    for file_name in documents:
        # noinspection PyBroadException
        try:
            org = hash_document(file_name)
        except FileNotFoundError:
            if get_global_state().verbose:
                print(f'Document file not found: {file_name}', file=sys.stderr)
        except IOError as ex:
            print(f'Error accessing document file "{file_name}": {ex}', file=sys.stderr)
        else:
            org_documents.append(org)

    current_hash_path = paths.new_dir_path / 'hashes-{:%Y%m%d%H%M%S}.json'.format(datetime.datetime.utcnow())
    with current_hash_path.open('w', encoding='UTF-8') as f:
        hash_files(org_documents, f)

    return current_hash_path


def stamp_files(current_hash_path: Optional[Path] = None) -> None:

    config = get_config()

    names = sorted([
        name for name in os.listdir(paths.new_dir_path)
        if re_hash_file_name.fullmatch(name)])

    def path_gen():

        if current_hash_path:
            yield current_hash_path

        for name in names:
            p = paths.new_dir_path / name
            if p != current_hash_path:
                yield p

    for hash_path in path_gen():

        ots_path = Path(str(hash_path) + '.ots')
        ots_bak_path = Path(str(hash_path) + '.ots.bak')

        args = [
            config['ots_command_path'],
            'stamp',
            str(hash_path)
        ]

        rc = subprocess.call(args, stdin=subprocess.DEVNULL)
        if rc != 0:
            print(f'"ots stamp" failed with exit code {rc}', file=sys.stderr)
            continue

        try:
            ots_path.rename(paths.stamped_dir_path / ots_path.name)
        except FileNotFoundError:
            continue

        for path in hash_path, ots_bak_path:
            try:
                path.rename(paths.stamped_dir_path / path.name)
            except FileNotFoundError:
                pass


def upgrade_files(current_hash_path: Optional[Path] = None) -> None:

    config = get_config()

    names = sorted([
        name for name in os.listdir(paths.stamped_dir_path)
        if re_hash_file_name.fullmatch(name)])

    for name in names:

        hash_path = paths.stamped_dir_path / name

        if hash_path == current_hash_path:
            continue

        ots_path = Path(str(hash_path) + '.ots')
        ots_bak_path = Path(str(hash_path) + '.ots.bak')

        try:
            age = time.time() - ots_path.stat().st_mtime
        except OSError:
            continue

        if age < 8 * 3600:
            continue

        args = [
            config['ots_command_path'],
            'upgrade',
            str(ots_path)
        ]

        rc = subprocess.call(args, stdin=subprocess.DEVNULL)
        if rc != 0:
            print(f'"ots upgrade" failed with exit code {rc}', file=sys.stderr)
            continue

        for path in hash_path, ots_path, ots_bak_path:
            try:
                path.rename(paths.complete_dir_path / path.name)
            except FileNotFoundError:
                pass


def quote_path(x: str) -> str:
    def repl(m):
        return '|' if m.group(0) == '/' else '`' + m.group(0)
    return re.sub(r'[/`|~]', repl, x)


def unquote_path(x: str) -> str:
    def repl(m):
        return '/' if m.group(0) == '|' else m.group(1)
    return re.sub(r'\||`(.)', repl, x)


@click.command()
@click.option(
    '-x', '--hash', 'hash_', is_flag=True,
    default=None,
    help='Hash the files listed in the configuration')
@click.option(
    '-p', '--process', is_flag=True,
    help='Stamp or upgrade any hash files that need processing')
@click.option(
    '-c', '--hash-only', is_flag=True,
    help='Just write generated hash file JSON to standard output')
@click.option(
    '-v', '--verbose', is_flag=True,
    help='Print more information')
@click.option(
    '-V', '--version', is_flag=True,
    help='Print the application version')
@click.argument('files', nargs=-1)
def main(
        hash_: bool,
        process: bool,
        hash_only: bool,
        verbose: bool,
        version: bool,
        files: List[str]):

    if version:
        from . import __version__ as version_string
        print(version_string)
        return

    get_global_state().verbose = verbose

    if hash_only:
        if hash_ or process:
            raise click.UsageError('-c/--hash-only cannot be combined with other options')
        if not files:
            files = get_config()['documents']
        hash_files((DocFile(Path(f)) for f in files), sys.stdout)
        return

    if files:
        raise click.UsageError('Arguments are only accepted in hash-only mode.')

    if hash_:
        process = True

    if not process:
        raise click.UsageError('Nothing to do. One of -x, -p, or -c is required.')

    create_directories()

    current_hash_path = None
    if hash_:
        current_hash_path = hash_documents()

    stamp_files(current_hash_path)
    upgrade_files()