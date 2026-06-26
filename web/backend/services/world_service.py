"""Read-only queries over the decoded world save dict.

Pure functions: input is the dumped ``level_dict`` (and optionally a character
name map), output is plain dicts matching the pydantic schemas. Every access is
defensive (``.get`` + ``try/except``) because raw save shapes drift across game
versions.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

CharacterNameMap = dict[str, str]


# ---- small unwrap helpers ---------------------------------------------------

def _u(node: Any, *path, default=None) -> Any:
    """Walk a chain of ``['value']``-and-key accesses, never raising.

    ``_u(x, 'a', 'b')`` returns ``x['a']['value']['b']['value']`` if present,
    tolerating the UE ``{'value': ...}`` wrappers at every step.
    """
    cur = node
    for key in path:
        if isinstance(cur, Mapping):
            cur = cur.get(key, default)
        else:
            return default
        if isinstance(cur, Mapping) and "value" in cur and len(cur) <= 4:
            cur = cur.get("value", cur)
    if isinstance(cur, Mapping) and "value" in cur and len(cur) <= 4:
        cur = cur.get("value", cur)
    return cur


def get_world_save_data(level_dict: dict) -> dict:
    return (
        level_dict.get("properties", {})
        .get("worldSaveData", {})
        .get("value", {})
    )


def get_tick(wsd: dict) -> int:
    try:
        return int(
            wsd["GameTimeSaveData"]["value"]["RealDateTimeTicks"]["value"]
        )
    except Exception:
        return 0


def _map_values(wsd: dict, key: str) -> list[dict]:
    """Return the inner ``value`` list of a ``{key: {value: [...]}}`` map."""
    node = wsd.get(key, {})
    if isinstance(node, dict):
        return node.get("value", []) or []
    return []


# ---- counts -----------------------------------------------------------------

def count_world(level_dict: dict) -> dict:
    wsd = get_world_save_data(level_dict)
    guilds = [g for g in _map_values(wsd, "GroupSaveDataMap")
              if _group_type(g) == "EPalGroupType::Guild"]
    players = sum(
        len(_gplayers(g)) for g in guilds
    )
    return {
        "guilds": len(guilds),
        "players": players,
        "bases": len(_map_values(wsd, "BaseCampSaveData")),
        "containers": len(_map_values(wsd, "ItemContainerSaveData")),
        "characters": len(_map_values(wsd, "CharacterSaveParameterMap")),
    }


# ---- guilds / players -------------------------------------------------------


def _group_type(g: dict) -> str:
    """Guild entries are ``{key, value: {GroupType: {value: {value: ...}}}}``."""
    try:
        return g["value"]["GroupType"]["value"]["value"]
    except Exception:
        return ""


def _gplayers(g: dict) -> list[dict]:
    try:
        return g["value"]["RawData"]["value"].get("players", []) or []
    except Exception:
        return []


def _gname(g: dict) -> str:
    try:
        return g["value"]["RawData"]["value"].get("guild_name", "Unnamed Guild")
    except Exception:
        return "Unnamed Guild"


def _gbase_ids(g: dict) -> list[str]:
    try:
        return [str(b) for b in g["value"]["RawData"]["value"].get("base_ids", [])]
    except Exception:
        return []


def _gadmin(g: dict) -> str | None:
    try:
        v = g["value"]["RawData"]["value"].get("admin_player_uid")
        return str(v) if v else None
    except Exception:
        return None


def list_guilds(level_dict: dict) -> list[dict]:
    wsd = get_world_save_data(level_dict)
    out = []
    for g in _map_values(wsd, "GroupSaveDataMap"):
        if _group_type(g) != "EPalGroupType::Guild":
            continue
        try:
            gid = str(g["key"])
        except Exception:
            gid = ""
        players = _gplayers(g)
        out.append({
            "id": gid,
            "name": _gname(g),
            "player_count": len(players),
            "base_count": len(_gbase_ids(g)),
            "leader_uid": _gadmin(g),
            "player_uids": [str(p.get("player_uid", "")) for p in players],
        })
    return out


def _fmt_last_seen(elapsed_s: float | None) -> str | None:
    if elapsed_s is None:
        return None
    if elapsed_s < 0:
        return "Unknown"
    days = int(elapsed_s // 86400)
    hours = int(elapsed_s % 86400 // 3600)
    mins = int(elapsed_s % 3600 // 60)
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def list_players(level_dict: dict) -> list[dict]:
    wsd = get_world_save_data(level_dict)
    tick = get_tick(wsd)
    out = []
    seen: set[str] = set()
    for g in _map_values(wsd, "GroupSaveDataMap"):
        if _group_type(g) != "EPalGroupType::Guild":
            continue
        gid = str(g["key"]) if g.get("key") else ""
        gname = _gname(g)
        for p in _gplayers(g):
            uid = str(p.get("player_uid", "")) or ""
            if not uid or uid in seen:
                continue
            seen.add(uid)
            info = p.get("player_info") or {}
            name = info.get("player_name", "Unknown")
            last = info.get("last_online_real_time")
            elapsed = None
            if isinstance(last, (int, float)) and tick:
                elapsed = (tick - last) / 10_000_000.0
            out.append({
                "uid": uid,
                "name": name,
                "guild_id": gid,
                "guild_name": gname,
                "last_seen_seconds": elapsed,
                "last_seen_text": _fmt_last_seen(elapsed),
            })
    return out


# ---- bases ------------------------------------------------------------------

def _translation(raw: dict) -> tuple[float, float, float] | None:
    try:
        t = raw["transform"]["translation"]
        return (float(t["x"]), float(t["y"]), float(t["z"]))
    except Exception:
        return None


def list_bases(level_dict: dict) -> list[dict]:
    wsd = get_world_save_data(level_dict)
    out = []
    for b in _map_values(wsd, "BaseCampSaveData"):
        try:
            raw = b["value"]["RawData"]["value"]
        except Exception:
            raw = {}
        gid = raw.get("group_id_belong_to")
        gid = str(gid) if gid else None
        out.append({
            "id": str(raw.get("id", b.get("key", ""))),
            "guild_id": gid,
            "guild_name": None,
            "location": _translation(raw),
            "worker_count": 0,
            "raw": {},
        })
    return out


def attach_guild_names(bases: list[dict], guilds: list[dict]) -> None:
    by_id = {g["id"].lower(): g["name"] for g in guilds}
    for b in bases:
        if b.get("guild_id"):
            b["guild_name"] = by_id.get(b["guild_id"].lower())


# ---- containers -------------------------------------------------------------

def list_containers(level_dict: dict, limit: int = 200) -> list[dict]:
    wsd = get_world_save_data(level_dict)
    out = []
    for c in _map_values(wsd, "ItemContainerSaveData"):
        v = c.get("value", {})
        belong = _u(v, "BelongInfo") or {}
        slot_num = _u(v, "SlotNum")
        try:
            slot_count = int(slot_num) if slot_num is not None else 0
        except Exception:
            slot_count = 0
        out.append({
            "id": str(_u(c, "key") or ""),
            "owner_player_uid": _norm_uid(belong.get("PlayerUId") if isinstance(belong, dict) else None),
            "guild_id": _norm_uid(belong.get("GroupId") if isinstance(belong, dict) else None),
            "slot_count": slot_count,
            "item_count": 0,
        })
        if limit and len(out) >= limit:
            break
    return out


def _norm_uid(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v)
    return s if s and s != "00000000-0000-0000-0000-000000000000" else None


# ---- pals -------------------------------------------------------------------

def _pal_field(sp: dict, key: str) -> Any:
    """Read a SaveParameter field, unwrapping value/ByteProperty nesting."""
    node = sp.get(key)
    if node is None:
        return None
    if isinstance(node, Mapping):
        if "value" in node:
            inner = node["value"]
            if isinstance(inner, Mapping) and "value" in inner and "type" in inner:
                return inner["value"]
            return inner
        return node
    return node


def list_pals(
    level_dict: dict,
    name_map: CharacterNameMap | None = None,
    limit: int = 300,
) -> list[dict]:
    wsd = get_world_save_data(level_dict)
    nm = name_map or {}
    out = []
    for ch in _map_values(wsd, "CharacterSaveParameterMap"):
        try:
            owner = _norm_uid(_u(ch, "key", "PlayerUId"))
            inst = str(_u(ch, "key", "InstanceId") or "")
        except Exception:
            owner, inst = None, ""
        try:
            sp = ch["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]
        except Exception:
            sp = {}
        cid = _pal_field(sp, "CharacterID") or ""
        cid_str = str(cid)
        display = nm.get(cid_str.lower(), cid_str) if cid_str else None
        level = _pal_field(sp, "Level")
        rank = _pal_field(sp, "Rank")
        try:
            level = int(level) if level is not None else None
        except Exception:
            level = None
        try:
            rank = int(rank) if rank is not None else None
        except Exception:
            rank = None
        out.append({
            "instance_id": inst,
            "character_id": cid_str,
            "display_name": display,
            "owner_uid": owner,
            "nickname": _pal_field(sp, "NickName"),
            "level": level,
            "rank": rank,
            "is_illegal": False,
        })
        if limit and len(out) >= limit:
            break
    return out
