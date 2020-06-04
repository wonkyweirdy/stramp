import codecs
import json
from pathlib import Path
from typing import Dict, List

from stramp.docstruct import DocFile
from stramp.paths import paths


_config_loaded = False

_config = {
    'ots_command_path': 'ots',
}

utf_8_codec = codecs.lookup('UTF-8')


def get_config() -> Dict:
    global _config_loaded
    if not _config_loaded:
        _config.update(json.loads(paths.config_path.read_text(encoding='UTF-8')))
        _config_loaded = True
    return _config


def get_config_documents() -> List[DocFile]:

    docs = [
        DocFile(
            Path(info['path']),
            file_format=info['format'],
            file_encoding=info.get('encoding', 'UTF-8'))
        for info in get_config()['documents']
    ]

    # Only UTF-8 is supported for now
    for doc in docs:
        if codecs.lookup(doc.file_encoding) != utf_8_codec:
            raise ValueError(f'Character encoding {doc.file_encoding!r} is not supported')

    return docs
