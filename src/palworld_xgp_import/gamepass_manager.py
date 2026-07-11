import datetime
import os
import re
import shutil
import tempfile
import uuid
from typing import Optional

from palworld_xgp_import.container_types import (
    ContainerIndex, ContainerFileList, FILETIME, Container,
)

SAVE_SUFFIXES = ("Level", "Level-01", "LocalData", "WorldOption")


CONTAINER_REGEX = re.compile(r"[0-9A-F]{16}_[0-9A-F]{32}$")

STEAM_SAVE_REQUIRED = ['Level.sav', 'LevelMeta.sav', 'LocalData.sav']
XGP_CONTAINER_REQUIRED = ['Level', 'LevelMeta']


def validate_steam_save(steam_dir: str) -> list[str]:
    """Check a Steam save directory for required files. Returns list of missing files."""
    missing = []
    for fname in STEAM_SAVE_REQUIRED:
        if not os.path.isfile(os.path.join(steam_dir, fname)):
            missing.append(fname)
    pdir = os.path.join(steam_dir, 'Players')
    if not os.path.isdir(pdir) or not any(f.endswith('.sav') for f in os.listdir(pdir)):
        missing.append('Players/<player>.sav')
    return missing


def validate_xgp_save(container_path: str, index: ContainerIndex) -> list[str]:
    """Check XGP container index for required container types. Returns list of missing types."""
    names = {c.container_name.split('-', 1)[1] if '-' in c.container_name else c.container_name
             for c in index.containers}
    missing = []
    for req in XGP_CONTAINER_REQUIRED:
        if not any(n == req or n.startswith(req) for n in names):
            missing.append(req)
    player_present = any('Players-' in c.container_name for c in index.containers)
    if not player_present:
        missing.append('Players-{uid}')
    return missing


def recompress_to_steam(data: bytes) -> bytes | None:
    """Fast binary recompress XGP (PLZ) → Steam (PLM). Returns compressed
    bytes on success, None if already Steam or format unknown (caller
    should fall back to SAV→JSON→SAV roundtrip)."""
    from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav
    try:
        magic = data[8:11]
        if magic == b'PlM':
            return data
        if magic == b'PlZ':
            raw_gvas, _ = decompress_sav_to_gvas(data)
            return compress_gvas_to_sav(raw_gvas, 49)
        return None
    except Exception:
        return None


def find_container_paths() -> list[str]:
    wgs = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs"
    )
    if not os.path.isdir(wgs):
        return []
    return [
        os.path.join(wgs, d) for d in os.listdir(wgs)
        if CONTAINER_REGEX.match(d)
    ]


def read_container_index(container_path: str) -> ContainerIndex:
    index_path = os.path.join(container_path, "containers.index")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"containers.index not found: {index_path}")
    with open(index_path, "rb") as f:
        return ContainerIndex.from_stream(f)


def validate_container_has_data(container_path: str, index: ContainerIndex, save_id: str) -> bool:
    level = _find_container_multi(index, save_id, "Level", "Level-01")
    if level is None:
        return False
    cdir = os.path.join(container_path, level.container_uuid.bytes_le.hex().upper())
    if not os.path.isdir(cdir):
        return False
    if not any(f.startswith("container.") for f in os.listdir(cdir)):
        return False
    return True

def _try_read_world_name(data: bytes) -> str:
    try:
        from palsav.gvas import GvasFile
        from palsav.paltypes import PALWORLD_TYPE_HINTS
        from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
        from palsav.core import decompress_sav_to_gvas

        raw, _ = decompress_sav_to_gvas(data)
        g = GvasFile.read(raw, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
        return g.properties.get("SaveData", {}).get("value", {}).get("WorldName", {}).get("value", "Unknown")
    except Exception:
        return None

def get_save_names(index: ContainerIndex, container_path: str = "") -> list[dict]:
    seen = {}
    for c in index.containers:
        parts = c.container_name.split("-", 1)
        save_id = parts[0]
        suffix = parts[1] if len(parts) > 1 else ""
        if save_id not in seen:
            seen[save_id] = {"save_id": save_id, "world_name": save_id}
        if suffix == "LevelMeta" and container_path:
            try:
                data = _read_container_data(container_path, c)
                name = _try_read_world_name(data)
                if name:
                    seen[save_id]["world_name"] = name
            except Exception:
                pass
    return list(seen.values())


def _find_container(index: ContainerIndex, save_id: str, suffix: str) -> Optional[Container]:
    target = f"{save_id}-{suffix}"
    for c in index.containers:
        if c.container_name == target:
            return c
    return None


def _find_container_multi(index: ContainerIndex, save_id: str, *suffixes: str) -> Optional[Container]:
    for s in suffixes:
        c = _find_container(index, save_id, s)
        if c is not None:
            return c
    return None


def _read_container_data(container_path: str, container: Container) -> bytes:
    cdir = os.path.join(container_path, container.container_uuid.bytes_le.hex().upper())
    clist_files = [f for f in os.listdir(cdir) if f.startswith("container.")]
    if not clist_files:
        raise FileNotFoundError(f"container.* not found in {cdir}")
    clist_path = os.path.join(cdir, sorted(clist_files)[0])
    with open(clist_path, "rb") as f:
        flist = ContainerFileList.from_stream(f)
    if flist.files:
        return flist.files[0].data
    return b""


def _read_container_data_by_name(container_path: str, index: ContainerIndex, save_id: str, suffix: str) -> Optional[bytes]:
    c = _find_container(index, save_id, suffix)
    if c is None:
        return None
    return _read_container_data(container_path, c)


def _read_container_data_by_name_multi(container_path: str, index: ContainerIndex, save_id: str, *suffixes: str) -> Optional[bytes]:
    for s in suffixes:
        data = _read_container_data_by_name(container_path, index, save_id, s)
        if data is not None:
            return data
    return None


def extract_save_to_temp(container_path: str, index: ContainerIndex, save_id: str, temp_dir: str) -> dict[str, str]:
    extracted = {}

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, *SAVE_SUFFIXES)
    if level_data:
        p = os.path.join(temp_dir, "Level.sav")
        with open(p, "wb") as f:
            f.write(level_data)
        extracted["Level.sav"] = p

    meta_data = _read_container_data_by_name(container_path, index, save_id, "LevelMeta")
    if meta_data:
        p = os.path.join(temp_dir, "LevelMeta.sav")
        with open(p, "wb") as f:
            f.write(meta_data)
        extracted["LevelMeta.sav"] = p

    local_data = _read_container_data_by_name(container_path, index, save_id, "LocalData")
    if local_data:
        p = os.path.join(temp_dir, "LocalData.sav")
        with open(p, "wb") as f:
            f.write(local_data)
        extracted["LocalData.sav"] = p

    world_opt = _read_container_data_by_name(container_path, index, save_id, "WorldOption")
    if world_opt:
        p = os.path.join(temp_dir, "WorldOption.sav")
        with open(p, "wb") as f:
            f.write(world_opt)
        extracted["WorldOption.sav"] = p

    players_dir = os.path.join(temp_dir, "Players")
    os.makedirs(players_dir, exist_ok=True)
    for c in index.containers:
        if not c.container_name.startswith(f"{save_id}-Players-"):
            continue
        uid = c.container_name[len(f"{save_id}-Players-"):]
        data = _read_container_data(container_path, c)
        if data:
            p = os.path.join(players_dir, f"{uid}.sav")
            with open(p, "wb") as f:
                f.write(data)
            extracted[f"Players/{uid}.sav"] = p

    return extracted


def cleanup_container_path(index: ContainerIndex, container_path: str) -> None:
    for entry in os.listdir(container_path):
        dir_path = os.path.join(container_path, entry)
        if not os.path.isdir(dir_path):
            continue
        if not any(f.startswith("container.") for f in os.listdir(dir_path)):
            continue
        matching = any(
            entry == c.container_uuid.bytes_le.hex().upper()
            for c in index.containers
        )
        if not matching:
            shutil.rmtree(dir_path, ignore_errors=True)


def save_to_container(
    container_path: str,
    index: ContainerIndex,
    new_save_id: str,
    level_data: bytes,
    meta_data: Optional[bytes],
    players_data: dict[str, bytes],
    local_data: Optional[bytes] = None,
    world_option_data: Optional[bytes] = None,
    world_name: str = "Modified World",
) -> None:
    now_ts = datetime.datetime.now().timestamp()
    cleanup_container_path(index, container_path)

    def _create_container_entry(suffix: str, data: bytes) -> Container:
        c_uuid = uuid.uuid4()
        f_uuid = uuid.uuid4()
        cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
        os.makedirs(cdir, exist_ok=True)

        with open(os.path.join(cdir, "container.1"), "wb") as f:
            f.write((4).to_bytes(4, "little"))
            f.write((1).to_bytes(4, "little"))
            name_bytes = "Data".encode("utf-16-le")
            f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
            f.write(b"\x00" * 16)
            f.write(f_uuid.bytes)

        data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
        with open(data_path, "wb") as f:
            f.write(data)

        return Container(
            container_name=f"{new_save_id}-{suffix}",
            cloud_id="",
            seq=1,
            flag=5,
            container_uuid=c_uuid,
            mtime=FILETIME.from_timestamp(now_ts),
            size=len(data),
        )

    index.containers.append(_create_container_entry("Level", level_data))
    if meta_data:
        index.containers.append(_create_container_entry("LevelMeta", meta_data))
    if local_data:
        index.containers.append(_create_container_entry("LocalData", local_data))
    if world_option_data:
        index.containers.append(_create_container_entry("WorldOption", world_option_data))
    for uid, pdata in players_data.items():
        index.containers.append(_create_container_entry(f"Players-{uid}", pdata))

    index.mtime = FILETIME.from_timestamp(now_ts)
    index.write_file(container_path)


def write_gvas_to_container(
    container_path: str, index: ContainerIndex, save_id: str,
    level_data: bytes,
    meta_data: Optional[bytes] = None,
    local_data: Optional[bytes] = None,
    world_option_data: Optional[bytes] = None,
    players_data: Optional[dict[str, bytes]] = None,
) -> None:
    """Write modified save data back into an existing XGP container,
    replacing only containers whose name starts with <save_id>-.
    Does not touch containers belonging to other save IDs."""
    import time as _t
    _t0 = _t.perf_counter()
    now_ts = datetime.datetime.now().timestamp()

    prefix = f"{save_id}-"
    old_count = len(index.containers)
    index.containers = [c for c in index.containers if not c.container_name.startswith(prefix)]
    removed = old_count - len(index.containers)
    _t1 = _t.perf_counter()
    print(f'  [write_gvas] filtered {removed} old containers: {_t1-_t0:.2f}s')

    def _create_entry(suffix: str, data: bytes) -> Container:
        _a = _t.perf_counter()
        c_uuid = uuid.uuid4()
        f_uuid = uuid.uuid4()
        cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
        os.makedirs(cdir, exist_ok=True)
        _b = _t.perf_counter()
        with open(os.path.join(cdir, "container.1"), "wb") as f:
            f.write((4).to_bytes(4, "little"))
            f.write((1).to_bytes(4, "little"))
            name_bytes = "Data".encode("utf-16-le")
            f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
            f.write(b"\x00" * 16)
            f.write(f_uuid.bytes)
        _c = _t.perf_counter()
        data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
        with open(data_path, "wb") as f:
            f.write(data)
        _d = _t.perf_counter()
        print(f'  [write_gvas] _create_entry({suffix}): mkdir={_b-_a:.2f}s container.1={_c-_b:.2f}s data={_d-_c:.2f}s data_len={len(data)}')
        return Container(
            container_name=f"{save_id}-{suffix}",
            cloud_id="", seq=1, flag=5,
            container_uuid=c_uuid,
            mtime=FILETIME.from_timestamp(now_ts),
            size=len(data),
        )

    _t2 = _t.perf_counter()
    index.containers.append(_create_entry("Level", level_data))
    _t3 = _t.perf_counter()
    print(f'  [write_gvas] Level entry: {_t3-_t2:.2f}s')
    if meta_data:
        _t3a = _t.perf_counter()
        index.containers.append(_create_entry("LevelMeta", meta_data))
        print(f'  [write_gvas] LevelMeta entry: {_t.perf_counter()-_t3a:.2f}s')
    if local_data:
        _t3b = _t.perf_counter()
        index.containers.append(_create_entry("LocalData", local_data))
        print(f'  [write_gvas] LocalData entry: {_t.perf_counter()-_t3b:.2f}s')
    if world_option_data:
        _t3c = _t.perf_counter()
        index.containers.append(_create_entry("WorldOption", world_option_data))
        print(f'  [write_gvas] WorldOption entry: {_t.perf_counter()-_t3c:.2f}s')
    if players_data:
        _t3d = _t.perf_counter()
        for uid, pdata in players_data.items():
            index.containers.append(_create_entry(f"Players-{uid}", pdata))
        print(f'  [write_gvas] {len(players_data)} player entries: {_t.perf_counter()-_t3d:.2f}s')
    _t4 = _t.perf_counter()
    index.mtime = FILETIME.from_timestamp(now_ts)
    index.write_file(container_path)
    _t5 = _t.perf_counter()
    print(f'  [write_gvas] write_file: {_t5-_t4:.2f}s')
    print(f'  [write_gvas] total: {_t5-_t0:.2f}s')


def convert_to_steam(index: ContainerIndex, container_path: str, save_id: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, *SAVE_SUFFIXES)
    if level_data:
        with open(os.path.join(output_dir, "Level.sav"), "wb") as f:
            f.write(level_data)

    meta_data = _read_container_data_by_name(container_path, index, save_id, "LevelMeta")
    if meta_data:
        with open(os.path.join(output_dir, "LevelMeta.sav"), "wb") as f:
            f.write(meta_data)

    local_data = _read_container_data_by_name(container_path, index, save_id, "LocalData")
    if local_data:
        with open(os.path.join(output_dir, "LocalData.sav"), "wb") as f:
            f.write(local_data)

    world_opt = _read_container_data_by_name(container_path, index, save_id, "WorldOption")
    if world_opt:
        with open(os.path.join(output_dir, "WorldOption.sav"), "wb") as f:
            f.write(world_opt)

    players_dir = os.path.join(output_dir, "Players")
    os.makedirs(players_dir, exist_ok=True)
    for c in index.containers:
        if not c.container_name.startswith(f"{save_id}-Players-"):
            continue
        uid = c.container_name[len(f"{save_id}-Players-"):]
        data = _read_container_data(container_path, c)
        if data:
            with open(os.path.join(players_dir, f"{uid}.sav"), "wb") as f:
                f.write(data)


def convert_to_gamepass_from_steam(steam_dir: str, container_path: str, world_name: str = "Imported World") -> str:
    index_path = os.path.join(container_path, "containers.index")
    if os.path.exists(index_path):
        with open(index_path, "rb") as f:
            index = ContainerIndex.from_stream(f)
    else:
        index = _create_empty_index(container_path)

    new_save_id = uuid.uuid4().hex.upper()

    level_path = os.path.join(steam_dir, "Level.sav")
    meta_path = os.path.join(steam_dir, "LevelMeta.sav")
    local_path = os.path.join(steam_dir, "LocalData.sav")
    world_opt_path = os.path.join(steam_dir, "WorldOption.sav")
    players_dir = os.path.join(steam_dir, "Players")

    def _create_entry(suffix, data):
        return _create_container_entry_raw(container_path, f"{new_save_id}-{suffix}", data)

    if os.path.exists(level_path):
        with open(level_path, "rb") as f:
            index.containers.append(_create_entry("Level", f.read()))

    if os.path.exists(meta_path):
        with open(meta_path, "rb") as f:
            index.containers.append(_create_entry("LevelMeta", f.read()))

    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            index.containers.append(_create_entry("LocalData", f.read()))

    if os.path.exists(world_opt_path):
        with open(world_opt_path, "rb") as f:
            index.containers.append(_create_entry("WorldOption", f.read()))

    if os.path.isdir(players_dir):
        for pf in sorted(os.listdir(players_dir)):
            if pf.endswith(".sav"):
                uid = pf.replace(".sav", "")
                with open(os.path.join(players_dir, pf), "rb") as f:
                    index.containers.append(_create_entry(f"Players-{uid}", f.read()))

    index.mtime = FILETIME.from_timestamp(datetime.datetime.now().timestamp())
    index.write_file(container_path)
    return new_save_id


def _create_empty_index(container_path: str) -> ContainerIndex:
    index = ContainerIndex(
        flag1=0,
        package_name="",
        mtime=FILETIME.from_timestamp(datetime.datetime.now().timestamp()),
        flag2=0,
        index_uuid="",
        unknown=0,
        containers=[],
    )
    return index


def _create_container_entry_raw(container_path: str, name: str, data: bytes) -> Container:
    c_uuid = uuid.uuid4()
    f_uuid = uuid.uuid4()
    cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
    os.makedirs(cdir, exist_ok=True)

    with open(os.path.join(cdir, "container.1"), "wb") as f:
        f.write((4).to_bytes(4, "little"))
        f.write((1).to_bytes(4, "little"))
        name_bytes = "Data".encode("utf-16-le")
        f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
        f.write(b"\x00" * 16)
        f.write(f_uuid.bytes)

    data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
    with open(data_path, "wb") as f:
        f.write(data)

    return Container(
        container_name=name,
        cloud_id="",
        seq=1,
        flag=5,
        container_uuid=c_uuid,
        mtime=FILETIME.from_timestamp(datetime.datetime.now().timestamp()),
        size=len(data),
    )
