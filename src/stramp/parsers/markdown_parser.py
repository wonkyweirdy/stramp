import datetime
import os
import re
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import marko
import marko.block
import marko.parser

from stramp.docstruct import DocFile, DocSection


class TrackingHeading(marko.block.Heading):

    override = True
    heading_matches = {}

    def __init__(self, match):
        super().__init__(match)
        headings, pos = TrackingHeading.heading_matches.pop(id(match))
        headings.append((pos, self.level))

    @classmethod
    def parse(cls, source):
        pos = source.pos
        m = super().parse(source)
        doc = source.root
        if not hasattr(doc, 'stramp_headings'):
            doc.stramp_headings = []
        TrackingHeading.heading_matches[id(m)] = doc.stramp_headings, pos
        return m


class TrackingParser(marko.parser.Parser):

    def __init__(self):
        super().__init__()
        self.add_element(TrackingHeading)


def get_raw_byte_offsets(pos_list: Iterable[int], text: str):
    # Recreate the raw byte positions of the input file.
    # The file positions used within Marko are character (not byte) positions, and
    # CR-LF sequences are converted to LF before the document text is processed.
    # The character encoding and line-ending conversions have to be accounted for.

    cr_lf_indexes = [m.start() for m in re.finditer(r'\r\n', text)]

    shift = 0
    adj_pos = 0
    raw_pos = 0

    for pos in pos_list:

        while shift < len(cr_lf_indexes) and cr_lf_indexes[shift] <= pos + shift:
            shift += 1

        prev_adj_pos = adj_pos
        adj_pos = pos + shift

        raw_pos += len(text[prev_adj_pos:adj_pos].encode('UTF-8'))

        yield raw_pos


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

    text = doc.file_bytes.decode('UTF-8')

    m = marko.Markdown(parser=TrackingParser)
    md_doc = m.parse(text)  # type: Any

    headings = md_doc.stramp_headings  # type: List[Tuple[int, int]]

    raw_positions = get_raw_byte_offsets((pos for pos, level in headings), text)

    sections = [DocSection(0, '(ROOT)', 0, len(doc.file_bytes))]

    for (pos, level), raw_pos in zip(headings, raw_positions):
        sections.append(DocSection(level, '', start_offset=raw_pos))

    doc.root_heading = link_sections(sections)
