---
name: pst-save-pipeline
description: Deep internals of the palsav save serialization engine + palooz Oodle bindings, and exactly how PST (palworld_aio GUI) consumes them. Load when touching any save parse/roundtrip/compression code, debugging roundtrip drift, editing rawdata decoders, or tracing the SAV<->GVAS<->JSON flow.
---

# PST Save Pipeline — palsav + palooz internals

palsav (pkg `palsav-flex` v0.2.0, MIT) = the save serialization engine. Fork of oMaN-Rod/palworld-save-tools, retuned with Oodle compression. palooz (separate sub-pkg under src/palsav/palooz/, v0.2.0, GPL-3.0) = compiled C++ Python bindings to the Oodle decompressor (Kraken-only compress + universal Oodle decompress), x64 + ARM64 via SIMDe.

## Layered architecture (bottom = bytes, top = JSON)
```
palooz (C++ ext)              raw Oodle compress/decompress
palsav.compressor             OozLib + Zlib; .sav container header parse/build
  ├ enums.py    SaveType{CNK=48,PLM=49,PLZ=50}, MagicBytes{PlZ,PlM,CNK}
  ├ __init__.py Compressor: _parse_sav_header, check_sav_format, build_sav
  ├ oozlib.py   OozLib: wraps palooz, Kraken/Normal level, loads platform lib
  └ zlib.py     Zlib: PLZ=double-zlib, single for CNK
palsav.core                  decompress_sav_to_gvas / compress_gvas_to_sav (public entry, dispatches on SaveType)
palsav.archive               FArchiveReader/FArchiveWriter (UE binary format, 809 lines — biggest file)
palsav.gvas                  GvasHeader + GvasFile (UE GVAS container)
palsav.paltypes              PALWORLD_TYPE_HINTS + PALWORLD_CUSTOM_PROPERTIES + DISABLED_PROPERTIES
palsav.rawdata.*             per-entity decode/encode (character, group, base_camp, work, map_object, ...)
palsav.json_tools            orjson dump/load + base64 byte-tag roundtripping
palsav.commands.*            CLI subcommands (convert, backup, diag, roundtrip_validation)
palsav.cli                   `palsav` CLI dispatcher (PYTHONHASHSEED=0 forced)
```

## The .sav container header
`uncompressed_len(4,LE) | compressed_len(4,LE) | magic(3) | save_type(1) | payload`
- CNK (0x30) has a NESTED header: first 12 bytes are outer, then a second (uncompressed_len, compressed_len, magic, type) at offset 12-24, data_offset=24. Handled in `Compressor._parse_sav_header`.
- Three formats: PLZ=double-zlib (original Steam), PLM=Oodle (newer), CNK=chunked/zlib.

## The GVAS container (gvas.py)
`GvasHeader`: magic 1396790855 (validated), save_game_version must be 3, custom_version_format must be 3, engine version tuple, custom_versions array, save_game_class_name (used to pick compression on write). `GvasFile`: header + properties dict + trailer (must be 4 zero bytes; logged if not — means incomplete parse). `read/load/write/dump` for both binary<->object and object<->dict.

## PALWORLD_CUSTOM_PROPERTIES — the dispatch table (paltypes.py)
Maps a dotted property PATH -> `(decode_fn, encode_fn)` pair from rawdata modules. When FArchiveReader hits that path while walking the property tree, it calls the custom decoder instead of the generic one. 17 registered paths, e.g.:
- `.worldSaveData.GroupSaveDataMap` → group
- `.worldSaveData.CharacterSaveParameterMap.Value.RawData` → character
- `.worldSaveData.ItemContainerSaveData.Value.RawData` → item_container
- `.worldSaveData.BaseCampSaveData.Value.RawData` → base_camp
- `.worldSaveData.WorkSaveData` → work
- `.worldSaveData.MapObjectSaveData` → map_object
- etc.

`PALWORLD_TYPE_HINTS` = path->type overrides for structurally ambiguous properties (disambiguates StructProperty vs Guid at specific paths). `DISABLED_PROPERTIES = {'.worldSaveData.BaseCampSaveData.Value.ModuleMap'}` — registered but skipped (likely broken for current game version). FArchiveReader checks this set before dispatching.

## The rawdata decode/encode pattern (character.py is canonical)
```
def decode(reader, type_name, size, path):
    # 1. read the raw ArrayProperty
    value = reader.property(type_name, size, path, nested_caller_path=path)
    # 2. extract the byte array
    char_bytes = value['value']['values']
    # 3. parse the entity-specific structure via an internal_copy reader
    value['value'] = decode_bytes(reader, char_bytes)
    return value

def decode_bytes(parent_reader, char_bytes):
    reader = parent_reader.internal_copy(bytes(char_bytes), debug=False)
    char_data = {'object': reader.properties_until_end(),
                 'unknown_bytes': reader.byte_list(4),
                 'group_id': reader.guid(),
                 'trailing_bytes': reader.byte_list(4)}
    if not reader.eof():
        char_data['trailing_unknown_bytes'] = reader.read_to_end()  # roundtrip-critical
    return char_data
```
**Roundtrip rule (sacred):** every trailing/unknown byte MUST be captured and re-emitted verbatim. The `trailing_unknown_bytes` field exists precisely so forward-compatible saves (new game-version fields appended) survive a roundtrip. This is the #1 source of roundtrip drift — see history.

## How PST (palworld_aio GUI) consumes palsav — THREE paths

**1. Direct import** (clean): `from palsav import json_tools` (bootup.py, i18n), `from palsav.gvas import GvasFile`, `from palsav.core import decompress_sav_to_gvas` (save_manager.py).

**2. Via `src/import_libs.py`** (star-import re-export shim): brings `palsav.archive.*`, `palsav.paltypes.*`, `palsav.gvas.*`, `palsav.json_tools.*`, `palsav.rawdata.group` into app namespace. Most palworld_aio modules inherit these symbols through import_libs.

**3. Via `palworld_aio/utils.py` wrappers** (the cleanest seam — use this):
- `sav_to_gvas_wrapper(path)` → decompress + GvasFile.read → wraps in `GvasFileWrapper` (dict-like adapter so the app edits `.properties` as a plain dict). Uses mmap for >100MB files.
- `wrapper_to_sav(wrapper, path)` → extracts underlying GvasFile → compresses → writes.
- `sav_to_gvasfile(path)` → returns raw GvasFile (no wrapper).
- `sav_to_json(path)` / `json_to_sav(j, path)` → full dict roundtrip.
- `gvasfile_to_sav(gvas_file, path)` → write a GvasFile back to .sav.

`constants.loaded_level_json` is a `GvasFileWrapper` — the entire app edits it in place, then `wrapper_to_sav` writes it back.

## SKP_PALWORLD_CUSTOM_PROPERTIES — the GUI's performance override (palobject.py:232)
PST clones `PALWORLD_CUSTOM_PROPERTIES` then OVERRIDES 6 paths with `(skip_decode, skip_encode)` NO-OPS (raw bytes pass through opaque):
- MapObject: WorldLocation, WorldRotation, WorldScale3D, Model.EffectMap
- FoliageGridSaveDataMap (entire map)
- MapObjectSpawnerInStageSaveData (entire)

**Why:** these are huge blobs the GUI never edits — skipping decode saves significant time/memory. **Consequence:** the GUI cannot edit those fields (they're opaque). The CLI (`palsav convert`) uses the FULL property table and decodes everything. **This is a deliberate CLI≠GUI divergence.** If someone needs to edit foliage/spawner/location data, they must use the CLI or remove the skip override.

## Compression selection on write (utils.py:70)
```python
t = 50 if 'Pal.PalworldSaveGame' in g.header.save_game_class_name else 49
```
50=PLZ(double-zlib), 49=PLM(Oodle). So world-class saves → zlib, others → Oodle. NOTE the lowercase 'w' in 'PalworldSaveGame' — verify actual UE class names are lowercase-matching (UE class names are often PascalCase like `PalWorldSaveGame`); if mismatched, format selection silently falls back to Oodle.

## History (the sacred-roundtrip theme)
- palsav began bundled with pyooz (Oodle submodule), then locally bundled.
- `ee362bb` (cyrix) — **THE pivotal commit**: replaced palsav core with "proven 1:1-roundtrip palworld_save_tools code" (copied 40 files). An earlier "modernized" core had BROKEN byte-exact roundtrip; this reverted to the proven code. Verified: player save 30,921 bytes 1:1, Level 4,215,854 bytes 1:1.
- `1e3eff6` (cyrix) — renamed pyooz→palooz, stripped to Kraken-only compress + universal Oodle decompress, removed ~288 unused SIMDe headers.
- Recent commits (1a9c328 guild integrity, 5152beb use_u8 fallback, 9ac23cc dynamic item IDs) are ALL about defending roundtrip fidelity against game-format drift.
- **Lesson:** any change to archive.py, a rawdata decoder, or the property dispatch MUST be validated with `pytest -m slow` (the 3.2MB V1 beta roundtrip) AND ideally a real-save byte diff. Roundtrip drift is the project's recurring failure mode.

## Validation tooling (palsav.commands)
- `roundtrip_validation.py` — SAV→JSON→SAV byte comparison.
- `diag.py` — read-only save diagnostics (header, format, property inventory).
- `resave_test.py` — resave + compare.
- `palsav validate <save>` / `palsav diag <save>` from CLI.

## Working rules
- To add a new game property: write a rawdata module with decode/encode, register in PALWORLD_CUSTOM_PROPERTIES (paltypes.py). Add type hints to PALWORLD_TYPE_HINTS if structurally ambiguous.
- To edit a skipped property in the GUI: remove/override its entry in SKP_PALWORLD_CUSTOM_PROPERTIES (palobject.py).
- ALWAYS run `pytest -m slow` after touching archive.py / rawdata / paltypes.
- palooz is a compiled C++ extension — platform-specific (win/linux-x64/linux-arm64/mac-x64/mac-arm64). Built via setup.py with -O3 -flto. Source in src/palsav/palooz/ooz/.