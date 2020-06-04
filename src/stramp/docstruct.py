import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from anytree import NodeMixin


@dataclass
class DocSection(NodeMixin):
    level: int
    text: str
    start_offset: int
    end_offset: int = 0


@dataclass
class DocFile:
    file_path: Path
    file_data_path: Optional[Path] = None
    file_read_datetime: Optional[datetime.datetime] = None
    file_stat: Optional[os.stat_result] = None
    file_format: str = 'org'
    file_encoding: str = 'UTF-8'
    file_bytes: Optional[bytes] = None
    root_heading: Optional[DocSection] = None
