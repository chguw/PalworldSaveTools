"""In-memory save state.

Holds the decoded Level.sav for the lifetime of the process. We keep both the
``GvasFile`` object (for byte-faithful re-encoding) and a cached ``dump()``
dict (the source of truth the read-only viewers query).

Single-user / local model: one save loaded at a time. A ``threading.Lock``
guards the heavy decode/encode paths since FastAPI serves requests on a
threadpool.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from palsav.gvas import GvasFile


@dataclass
class LoadedSave:
    filename: str
    save_dir: str
    players_dir: str
    save_type: int          # value returned by decompress_sav_to_gvas; reused on encode
    class_name: str
    file_size: int
    loaded_at: float
    gvas: GvasFile          # for re-encode
    level_dict: dict[str, Any] = field(default_factory=dict)


class SaveState:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._save: LoadedSave | None = None

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    def is_loaded(self) -> bool:
        return self._save is not None

    def get(self) -> LoadedSave | None:
        return self._save

    def require(self) -> LoadedSave:
        if self._save is None:
            raise RuntimeError("No save loaded")
        return self._save

    def set(self, save: LoadedSave) -> None:
        with self._lock:
            self._save = save

    def clear(self) -> None:
        with self._lock:
            self._save = None


save_state = SaveState()
