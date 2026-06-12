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


CONTAINER_REGEX = re.compile(r"[0-9A-F]{16}_[0-9A-F]{32}$")


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
        from palsav.palsav import decompress_sav_to_gvas
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

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, "Level", "Level-01")
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
    for uid, pdata in players_data.items():
        index.containers.append(_create_container_entry(f"Players-{uid}", pdata))

    index.mtime = FILETIME.from_timestamp(now_ts)
    index.write_file(container_path)


def convert_to_steam(index: ContainerIndex, container_path: str, save_id: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, "Level", "Level-01")
    if level_data:
        with open(os.path.join(output_dir, "Level.sav"), "wb") as f:
            f.write(level_data)

    meta_data = _read_container_data_by_name(container_path, index, save_id, "LevelMeta")
    if meta_data:
        with open(os.path.join(output_dir, "LevelMeta.sav"), "wb") as f:
            f.write(meta_data)

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
    players_dir = os.path.join(steam_dir, "Players")

    def _create_entry(suffix, data):
        return _create_container_entry_raw(container_path, f"{new_save_id}-{suffix}", data)

    if os.path.exists(level_path):
        with open(level_path, "rb") as f:
            index.containers.append(_create_entry("Level", f.read()))

    if os.path.exists(meta_path):
        with open(meta_path, "rb") as f:
            index.containers.append(_create_entry("LevelMeta", f.read()))

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
