#!/usr/bin/python3

import datetime
import hashlib
import io
import json
from typing import Iterable, Union

from anytree import PreOrderIter
from typing.io import TextIO

from .docstruct import DocFile


def write_file_hash_json(doc: DocFile, out: TextIO, hash_algorithm: str = 'sha256'):

    assert doc.root_heading is not None

    epoch = datetime.datetime(1970, 1, 1)
    mtime_dt = epoch + datetime.timedelta(microseconds=doc.file_stat.st_mtime_ns // 1000)
    mtime_str = mtime_dt.isoformat(timespec='microseconds') + 'Z'

    metadata = {
        'file_path': str(doc.file_path),
        'file_date': mtime_str,
        'read_datetime': doc.file_read_datetime.isoformat(timespec='microseconds') + 'Z',
        'hash_algorithm': hash_algorithm,
    }

    out.write('{\n')
    for k, v in metadata.items():
        out.write(f'{json.dumps(k)}: {json.dumps(v)},\n')

    out.write('"range_hashes": [\n')

    first = True

    for h in PreOrderIter(doc.root_heading):

        if not first:
            out.write(',\n')
        first = False

        record = [
            h.start_offset,
            h.end_offset,
            hashlib.new(hash_algorithm, doc.file_bytes[h.start_offset:h.end_offset]).hexdigest(),
            # h.text,
        ]
        out.write(json.dumps(record))

    out.write(']}\n')


def hash_files(docs: Iterable[DocFile], out: TextIO):

    out.write('{\n')
    out.write('"generator": "stramp",\n')
    out.write('"documents": [\n')

    first = True
    for doc in docs:

        if doc.file_format == 'org':
            from stramp.parsers.org_parser import load_file as load_org_file
            load_org_file(doc)
        elif doc.file_format in ('commonmark', 'markdown'):
            from stramp.parsers.markdown_parser import load_file as load_markdown_file
            load_markdown_file(doc)
        else:
            raise ValueError(f'Unsupported file format {doc.file_format!r}')

        with io.StringIO() as file_json:  # type: Union[TextIO, io.StringIO]

            write_file_hash_json(doc, file_json)

            if not first:
                out.write(',\n')
            first = False
            out.write(file_json.getvalue())

    out.write(']}\n')
