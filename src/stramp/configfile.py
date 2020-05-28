
import json
from typing import Dict

from stramp.paths import paths

_config_loaded = False

_config = {
    'ots_command_path': 'ots',
}


def get_config() -> Dict:
    global _config_loaded
    if not _config_loaded:
        _config.update(json.loads(paths.config_path.read_text(encoding='UTF-8')))
        _config_loaded = True
    return _config
