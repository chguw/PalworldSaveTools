"""SAV <-> GVAS <-> dict round-trip via the installed palsav engine.

Uses the FULL ``PALWORLD_CUSTOM_PROPERTIES`` table (CLI-grade fidelity), not
the GUI's 6-path no-op override. The save_type reported by decompression is
reused on encode for byte-faithful round-trips.
"""

from __future__ import annotations

import io
from pathlib import Path

from palsav.core import compress_gvas_to_sav, decompress_sav_to_gvas
from palsav.gvas import GvasFile
from palsav.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS

# Module-level constants reused on every read/write.
_TYPE_HINTS = PALWORLD_TYPE_HINTS
_CUSTOM_PROPS = PALWORLD_CUSTOM_PROPERTIES


class SaveDecodeError(Exception):
    """Raised when a .sav cannot be decompressed/parsed."""


def decode_bytes(data: bytes) -> tuple[GvasFile, int, dict]:
    """Decode raw SAV bytes into (gvas, save_type, level_dict).

    Raises ``SaveDecodeError`` on any palsav failure.
    """
    try:
        raw_gvas, save_type = decompress_sav_to_gvas(data)
        gvas = GvasFile.read(
            raw_gvas, _TYPE_HINTS, _CUSTOM_PROPS, allow_nan=True
        )
    except SaveDecodeError:
        raise
    except Exception as exc:  # palsav raises a variety of errors
        raise SaveDecodeError(f"Failed to decode save: {exc}") from exc
    level_dict = gvas.dump()
    return gvas, save_type, level_dict


def decode_file(path: str | Path) -> tuple[GvasFile, int, dict, int]:
    """Decode a .sav on disk. Returns (gvas, save_type, level_dict, file_size)."""
    p = Path(path)
    data = p.read_bytes()
    gvas, save_type, level_dict = decode_bytes(data)
    return gvas, save_type, level_dict, len(data)


def encode_bytes(gvas: GvasFile, save_type: int) -> bytes:
    """Re-encode a GvasFile back into SAV bytes using the original save_type."""
    try:
        return compress_gvas_to_sav(gvas.write(_CUSTOM_PROPS), save_type)
    except Exception as exc:
        raise SaveDecodeError(f"Failed to encode save: {exc}") from exc


def encode_to_stream(gvas: GvasFile, save_type: int) -> io.BytesIO:
    """Encode and wrap in a seekable stream (for StreamingResponse)."""
    return io.BytesIO(encode_bytes(gvas, save_type))


def save_type_for_class(class_name: str) -> int:
    """Heuristic save_type from the save-game class name (fallback only).

    World saves use PLZ (50); everything else PLM/Oodle (49). We prefer the
    save_type captured during decompression, which is always exact.
    """
    cn = class_name or ""
    if "Pal.PalworldSaveGame" in cn or "Pal.PalLocalWorldSaveGame" in cn:
        return 50
    return 49
