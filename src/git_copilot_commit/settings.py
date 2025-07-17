"""
Settings management using XDG Base Directory specification.
"""

import json
from typing import Optional, Dict, Any

from xdg_base_dirs import (
    xdg_cache_home,
    xdg_config_home,
    xdg_data_home,
    xdg_state_home,
)


class Settings:
    """Manages application settings using XDG Base Directory specification."""

    APP_NAME = "git-copilot-commit"

    def __init__(self):
        self.config_dir = xdg_config_home() / self.APP_NAME
        self.data_dir = xdg_data_home() / self.APP_NAME
        self.cache_dir = xdg_cache_home() / self.APP_NAME
        self.state_dir = xdg_state_home() / self.APP_NAME

        self.config_file = self.config_dir / "config.json"

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't write

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self._save_config()

    def delete(self, key: str) -> None:
        """Delete a configuration value."""
        if key in self._config:
            del self._config[key]
            self._save_config()

    @property
    def default_model(self) -> Optional[str]:
        """Get the default model."""
        return self.get("default_model")

    @default_model.setter
    def default_model(self, model: str) -> None:
        """Set the default model."""
        self.set("default_model", model)

    def clear_cache(self) -> None:
        """Clear the cache directory."""
        for file in self.cache_dir.glob("*"):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                import shutil

                shutil.rmtree(file)
