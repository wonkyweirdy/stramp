
import datetime
import os
import re
from typing import List, Optional, Sequence

from stramp.docstruct import DocFile, DocSection

# https://orgmode.org/worg/dev/org-syntax.html
re_heading = re.compile(br'(?m)^(\*+)[^\S\r\n](\S.*)$')
re_greater_block_delimiter = re.compile(br'(?mi)^[^\S\r\n]*#\+(begin|end)_(\S+)(?:[^\S\r\n].*)?$')


def find_headings(data: bytes) -> List[DocSection]:

    headings = [DocSection(
        text='(ROOT)',
        level=0,
        start_offset=0,
        end_offset=len(data))]

    i = 0
    while i < len(data):

        m_heading = re_heading.search(data, i)
        m_block = re_greater_block_delimiter.search(data, i)

        if m_heading is None and m_block is None:
            break

        if m_block is not None and (m_heading is None or m_block.start() < m_heading.start()):
            i = m_block.end()
            while i < len(data):
                m = re_greater_block_delimiter.search(data, i)
                if m is None:
                    i = len(data)
                    break
                i = m.end()
                if m[1].lower() == b'end' and m[2].lower() == m_block[2].lower():
                    break
            continue

        if m_heading is not None:
            headings.append(DocSection(
                text=m_heading[2].decode('UTF-8'),
                level=len(m_heading[1]),
                start_offset=m_heading.start()))
            i = m_heading.end()

    return headings


def link_sections(headings: Sequence[DocSection]) -> DocSection:

    h_prev = None  # type: Optional[DocSection]
    root = None  # type: Optional[DocSection]

    for h in headings:

        if h.level == 0:
            # root
            assert h_prev is None
            root = h

        elif h.level > h_prev.level:
            # Descendant of h_prev
            h.parent = h_prev
            for level in range(h_prev.level + 1, h.level):
                hx = DocSection(level, '', h_prev.start_offset)
                hx.parent = h.parent
                h.parent = hx

        else:

            hx = h_prev.parent
            while hx.level > h.level - 1:
                hx = hx.parent
            h.parent = hx

            hx = h_prev
            while hx.level >= h.level:
                hx.end_offset = h.start_offset
                hx = hx.parent

        h_prev = h

    hx = h_prev
    while hx is not None:
        hx.end_offset = root.end_offset
        hx = hx.parent

    return root


def load_file(doc: DocFile):

    if doc.file_data_path is None:
        doc.file_data_path = doc.file_path

    with doc.file_data_path.open('rb') as f:
        doc.file_bytes = f.read()
        doc.file_stat = os.stat(f.fileno())

    doc.file_read_datetime = datetime.datetime.utcnow()

    sections = find_headings(doc.file_bytes)
    doc.root_heading = link_sections(sections)
