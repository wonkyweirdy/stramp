#!/usr/bin/python3

import datetime
import hashlib
import io
import json
from typing import Iterable, Union

from anytree import PreOrderIter
from typing.io import TextIO

from .orgfile import load_org_file
from .docstruct import DocFile


def write_file_hash_json(org: DocFile, out: TextIO, hash_algorithm: str = 'sha256'):

    epoch = datetime.datetime(1970, 1, 1)
    mtime_dt = epoch + datetime.timedelta(microseconds=org.file_stat.st_mtime_ns // 1000)
    mtime_str = mtime_dt.isoformat(timespec='microseconds') + 'Z'

    metadata = {
        'file_path': str(org.file_path),
        'file_date': mtime_str,
        'read_datetime': org.file_read_datetime.isoformat(timespec='microseconds') + 'Z',
        'hash_algorithm': hash_algorithm,
    }

    out.write('{\n')
    for k, v in metadata.items():
        out.write(f'{json.dumps(k)}: {json.dumps(v)},\n')

    out.write('"range_hashes": [\n')

    first = True

    for h in PreOrderIter(org.root_heading):

        if not first:
            out.write(',\n')
        first = False

        record = [
            h.start_offset,
            h.end_offset,
            hashlib.new(hash_algorithm, org.file_bytes[h.start_offset:h.end_offset]).hexdigest(),
            # h.text,
        ]
        out.write(json.dumps(record))

    out.write(']}\n')


def hash_files(org_docs: Iterable[DocFile], out: TextIO):

    out.write('{\n')
    out.write('"generator": "stramp",\n')
    out.write('"documents": [\n')

    first = True
    for org in org_docs:

        load_org_file(org)

        with io.StringIO() as file_json:  # type: Union[TextIO, io.StringIO]

            write_file_hash_json(org, file_json)

            if not first:
                out.write(',\n')
            first = False
            out.write(file_json.getvalue())

    out.write(']}\n')

