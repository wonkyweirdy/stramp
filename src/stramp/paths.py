from pathlib import Path


class Paths:

    app_dir_path = Path.home() / '.stramp'

    @property
    def data_dir_path(self): return self.app_dir_path / 'data'

    @property
    def new_dir_path(self): return self.app_dir_path / 'new'

    @property
    def stamped_dir_path(self): return self.app_dir_path / 'stamped'

    @property
    def complete_dir_path(self): return self.app_dir_path / 'complete'

    @property
    def config_path(self): return self.app_dir_path / 'config.json'


paths = Paths()
