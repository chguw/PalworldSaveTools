---
name: pst-binary-schemas
description: Reverse-engineered binary schemas for Booth (ItemBooth/PalBooth) and Guild rawdata in palsav. Lock flags, V1_MARKER handling, _u8_flag semantics, and roundtrip rules. Load when touching map_concrete_model.py or group.py decoders, booth/guild lock features, or debugging roundtrip drift.
---

# PST Binary Schemas — Booth & Guild

## Booth Lock Schema (`src/palsav/palsav/rawdata/map_concrete_model.py`)

### ItemBooth `trailing_bytes` (20B) -> 3 fields
RE'd by comparing unlocked vs locked Level.sav byte diffs:
```
unlocked: 000000000000000000000000 00 0000000
locked:   000000000000000000000000 01 0000000
                                    ^^ byte[12]=1
```
- `unknown_before_lock` (12B): opaque prefix
- `is_private_lock` (1B u8): **0=unlocked, 1=locked** — THIS controls the lock state
- `unknown_after_lock` (7B): opaque suffix

### PalBooth `unknown_bytes` (236B) -> 3 fields
```
unlocked byte[224]: 00
locked   byte[224]: 01
```
- `unknown_prefix` (224B)
- `is_private_lock` (1B u8): 0=unlocked, 1=locked
- `unknown_suffix` (11B)

### KEY: `private_lock_player_uid` is identical (non-zero) in BOTH locked & unlocked. Lock state is NOT that GUID — it's `is_private_lock`.

### Unlock function (`func_manager.py:748-782`)
- `deep_unlock` SKIPS both booth types
- Sets `is_private_lock = 0` on booth RawData dicts directly
- Does NOT zero `private_lock_player_uid` on booths (game needs it non-zero)

## Guild Binary Format — V1_MARKER (`src/palsav/palsav/rawdata/group.py`)

### Problem: pre-V1 bytes
Newer Palworld versions prepend ~480 bytes BEFORE the known `V1_MARKER` (`02 00 00 00 02 03 00 00 00 00`) in the guild binary tail. Old code checked `post_unk2[:10] == V1_MARKER` — missed when marker not at offset 0. try/except silently set `players: []`.

### Fix (commit 667370dd)
- **Decode:** `post_unk2[:10] == V1_MARKER` -> `post_unk2.find(V1_MARKER) >= 0`
- Pre-marker bytes saved as `_pre_v1_bytes` for roundtrip
- `_raw_tail` fallback uses `original_tail` (unmodified)

### v2 Guild Tail (2026-07 update, `group.py`)
New decoder `_read_guild_tail_v2` (line 62) replaces the old `_u8_flag`‑based player entries with a `role` field and a `role_permissions` array. The decoder tries v2 first; if it overshoots EOF, falls back to v1.

#### v2 player entry (`guild_player_info_reader`)
- `player_uid`: guid
- `player_info`: `{last_online_real_time: i64, player_name: fstring}`
- `role`: byte — `1`=admin/leader, `2`=submaster/officer, `3`=member, `4`=unknown

#### v2 guild tail fields
- `guild_chest_allowed_roles`: `tarray(byte)` — which roles can access chests
- `unknown_i32`: i32
- `admin_player_uid`: guid
- `players`: `tarray(guild_player_info_reader)`
- `role_permissions`: `tarray({role: byte, permissions: tarray(byte)})`
- `trailing_bytes`: 4 bytes

#### Encoder key (line 224)
```python
if "role_permissions" in p:
    # writes v2 format with role per player
else:
    # writes v1 format (no role field)
```

### `_u8_flag` → `role` migration (commit b5eac6bd)
The v2 encoder writes `p['role']` via `guild_player_info_writer`, but all manager functions were setting `p['_u8_flag']` — a key the encoder never reads. Silent data loss on every roundtrip.

**Files fixed:**
- `guild_manager.py`: `move_player_to_guild` + `make_member_leader` — `_u8_flag` → `role`
- `func_manager.py`: `delete_inactive_players`, `delete_duplicated_players`, `delete_unreferenced_data` — `_u8_flag` → `role`
- `data_manager.py`: `delete_player` — `_u8_flag` → `role`
- `character_transfer.py:1078`: fallback player entry missing `role` → added `'role': 1` to prevent KeyError on v2 roundtrip

**Role values** (same as old `_u8_flag`):
- `1` = guild master/admin
- `2` = submaster/officer
- `3` = regular member

## Debug Pattern
To inspect guild binary tail: convert Level.sav to JSON, load with `json_tools.load()`, search for `V1_MARKER` in `_raw_tail` hex. If at offset > 0, guild format was extended.

## Type Hints & Binary Schema Debugging

### How type hints work (`src/palsav/palsav/paltypes.py`)

`PALWORLD_TYPE_HINTS` maps GVAS property paths to struct type names. Used by `FArchiveReader.get_type_or()` when decoding `MapProperty`/`ArrayProperty` entries:

```python
# In _read_MapProperty:
if key_type == 'StructProperty':
    key_struct_type = self.get_type_or(key_path, 'Guid')  # default Guid for keys
if value_type == 'StructProperty':
    value_struct_type = self.get_type_or(value_path, 'StructProperty')  # default property bag
```

The default fallback differs:
- **Map keys** default to `Guid` (16 bytes) — most common key type
- **Map values** default to `StructProperty` (property bag until `None`) — most common value type
- **Array elements** default to `Guid` (set via struct type hint in array header)

### Debugging wrong type hints — step by step

When a save partially parses (some properties missing), the root cause is often a wrong type hint causing under/over-consumption.

**1. Convert to JSON, check which properties are missing**
```bash
uv run python -m palsav.cli convert save.sav --force
python -c "import json; d=json.load(open('save.sav.json')); print(list(d['properties']))"
```

**2. Trace the parser with a monkey-patch**
Add debug to `properties_until_end` to log every property read:
```python
_orig = FArchiveReader.properties_until_end
def _trace(self, path=''):
    pos = self.data.tell()
    name = self.fstring()
    if name in ('None',''): return {}
    tn = self.fstring()
    sz = self.u64()
    print(f'  [{pos}] name={name!r} type={tn!r} size={sz}')
    self.data.seek(pos)  # rewind for real read
    return _orig(self, path)
FArchiveReader.properties_until_end = _trace
```

**3. Find the map/array entry where over-consumption starts**
The last successfully-read property before the gap reveals which container has wrong hints. Dump entry count and first few keys:
```python
mp = save['SomeMap']
print(len(mp['value']), mp['value'][0]['key'])
```
Garbage keys (binary-looking UUIDs or mid-string fragments) indicate desync.

**4. Dump raw bytes of the failing map header + first entry**
```python
pos = <map start offset>
# skip property header (name + type + size)
nlen = struct.unpack('<i', data[pos:pos+4])[0]; pos += 4 + nlen
tlen = struct.unpack('<i', data[pos:pos+4])[0]; pos += 4 + tlen
psize = struct.unpack('<Q', data[pos:pos+8])[0]; pos += 8
# now at map header
klen = struct.unpack('<i', data[pos:pos+4])[0]
key_type = data[pos+4:pos+4+klen-1].decode('ascii')
vlen = struct.unpack('<i', data[pos+4+klen:pos+8+klen])[0]
val_type = data[pos+8+klen:pos+8+klen+vlen-1].decode('ascii')
print(f'key_type={key_type!r} value_type={val_type!r}')
```

**5. Compare actual data against hint assumption**
- If key_type='StructProperty' but hint says 'Guid': the struct WILL be read as 16 bytes. The rest of the struct's properties leak into the value field and subsequent entries → cascade failure.
- Fix: change hint to 'StructProperty' in `paltypes.py`.

### Known cases

| Path | Old hint | Correct hint | Reason |
|---|---|---|---|
| `.SaveData.Local_MaxFriendshipPalIds.Key` | `Guid` | `StructProperty` | Key contains `PlayerUId` property bag, not a bare 16-byte GUID |
| `.SaveData.Local_MaxFriendshipPalIds.Value` | `StructProperty` | (unused — data says `IntProperty`) | Value type from data is `IntProperty`, hint only applies when data says `StructProperty` |

### Key insight

The map HEADER (written by UE) stores actual `key_type`/`value_type` as fstrings. The type HINT in `paltypes.py` only matters when the header says `StructProperty` — it tells the parser WHICH struct type to use. A wrong hint causes the fixed-size reader (Guid = 16B) to under-consume while a property-bag reader (properties_until_end) would correctly consume the full structure, or vice versa.

