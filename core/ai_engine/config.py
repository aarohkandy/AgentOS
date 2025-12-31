import os
import configparser
from pathlib import Path

# Constants
DEFAULT_SOCKET_PATH = "/tmp/cosmic-ai.sock"
DEFAULT_LOG_FILE = "cosmic-ai.log"

class Config:
    def __init__(self, config_path="config/cosmic-os.conf"):
        self.config = configparser.ConfigParser()
        self.config_path = Path(config_path)
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            # Defaults will be handled by the caller or a separate default generator
            pass
        else:
            self.config.read(self.config_path)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def get_boolean(self, section, key, fallback=False):
        return self.config.getboolean(section, key, fallback=fallback)

    def get_int(self, section, key, fallback=0):
        return self.config.getint(section, key, fallback=fallback)

    def get_float(self, section, key, fallback=0.0):
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (ValueError, TypeError):
            return fallback

    def get_list(self, section, key, fallback=None):
        val = self.config.get(section, key, fallback=fallback)
        if val and isinstance(val, str):
            # rudimentary list parsing from string like "['a', 'b']" or "a, b"
            # For robustness we might want json parsing or standard comma split
            # Using simple comma split for now
            return [x.strip() for x in val.strip("[]").split(",")]
        return val

