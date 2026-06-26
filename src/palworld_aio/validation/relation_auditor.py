def _norm(s: str) -> str:
    return str(s).replace('-', '').lower() if s else ''


def audit_relations(level_json: dict) -> list[str]:
    errors = []
    wsd = level_json['properties']['worldSaveData']['value']

    guild_ids = _collect_guild_ids(wsd)
    instance_ids = _collect_instance_ids(wsd)
    container_ids = _collect_container_ids(wsd)
    dynamic_item_ids = _collect_dynamic_item_ids(wsd)

    _check_pal_guild_ids(wsd, guild_ids, errors)
    _check_pal_owner_ids(wsd, errors)
    _check_pal_instance_ids(wsd, instance_ids, errors)
    _check_guild_handle_ids(wsd, instance_ids, errors)
    _check_guild_base_ids(wsd, guild_ids, errors)
    _check_map_object_container_ids(wsd, container_ids, errors)
    _check_dynamic_item_links(wsd, dynamic_item_ids, errors)

    return errors


def _collect_guild_ids(wsd: dict) -> set:
    ids = set()
    for g in wsd.get('GroupSaveDataMap', {}).get('value', []):
        gid = _norm(g.get('key', ''))
        if gid:
            ids.add(gid)
    return ids


def _collect_instance_ids(wsd: dict) -> set:
    ids = set()
    for entry in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
        try:
            inst = entry['key'].get('InstanceId', {}).get('value', '')
            if inst:
                ids.add(_norm(inst))
        except Exception:
            pass
    return ids


def _collect_container_ids(wsd: dict) -> set:
    ids = set()
    for cont in wsd.get('ItemContainerSaveData', {}).get('value', []):
        cid = _norm(cont.get('key', {}).get('ID', {}).get('value', ''))
        if cid:
            ids.add(cid)
    for cont in wsd.get('CharacterContainerSaveData', {}).get('value', []):
        cid = _norm(cont.get('key', {}).get('ID', {}).get('value', ''))
        if cid:
            ids.add(cid)
    return ids


def _collect_dynamic_item_ids(wsd: dict) -> set:
    ids = set()
    for entry in wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', []):
        local_id = entry.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world', '')
        if local_id:
            ids.add(str(local_id))
    return ids


def _check_pal_guild_ids(wsd: dict, guild_ids: set, errors: list[str]) -> None:
    for entry in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            gid = sp.get('group_id', {}).get('value', '')
            if gid:
                norm_gid = _norm(gid)
                if norm_gid and norm_gid not in guild_ids:
                    char_name = sp.get('NickName', {}).get('value', '') or sp.get('CharacterID', {}).get('value', '?')
                    errors.append(f"Pal '{char_name}' has group_id={gid} which does not match any known guild")
        except Exception:
            pass


def _check_pal_owner_ids(wsd: dict, errors: list[str]) -> None:
    for entry in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            owner = sp.get('OwnerPlayerUId', {}).get('value', '')
            is_player = sp.get('IsPlayer', {}).get('value', False)
            if owner and not is_player:
                norm_owner = _norm(owner)
                owner_found = False
                for ch in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
                    try:
                        ch_sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
                        if ch_sp.get('IsPlayer', {}).get('value', False):
                            puid = ch.get('key', {}).get('PlayerUId', {}).get('value', '')
                            if _norm(puid) == norm_owner:
                                owner_found = True
                                break
                    except Exception:
                        pass
                if not owner_found:
                    char_id = sp.get('CharacterID', {}).get('value', '?')
                    errors.append(f"Pal '{char_id}' has OwnerPlayerUId={owner} but no player with that UID exists")
        except Exception:
            pass


def _check_pal_instance_ids(wsd: dict, instance_ids: set, errors: list[str]) -> None:
    seen = {}
    for entry in wsd.get('CharacterSaveParameterMap', {}).get('value', []):
        try:
            inst = entry['key'].get('InstanceId', {}).get('value', '')
            norm_inst = _norm(inst)
            if norm_inst and norm_inst in seen:
                char_id1 = '?'
                char_id2 = '?'
                try:
                    char_id1 = entry['value']['RawData']['value']['object']['SaveParameter']['value'].get('CharacterID', {}).get('value', '?')
                except Exception:
                    pass
                try:
                    seen_entry = seen[norm_inst]
                    char_id2 = seen_entry['value']['RawData']['value']['object']['SaveParameter']['value'].get('CharacterID', {}).get('value', '?')
                except Exception:
                    pass
                errors.append(f"Duplicate InstanceId {inst} on characters '{char_id1}' and '{char_id2}'")
            elif norm_inst:
                seen[norm_inst] = entry
        except Exception:
            pass


def _check_guild_handle_ids(wsd: dict, instance_ids: set, errors: list[str]) -> None:
    for g in wsd.get('GroupSaveDataMap', {}).get('value', []):
        try:
            handles = g['value']['RawData']['value'].get('individual_character_handle_ids', [])
            for h in handles:
                guid = _norm(h.get('guid', '') if isinstance(h, dict) else '')
                if guid and guid not in instance_ids:
                    errors.append(f"Guild has handle {guid} which does not match any character InstanceId")
        except Exception:
            pass


def _check_guild_base_ids(wsd: dict, guild_ids: set, errors: list[str]) -> None:
    for g in wsd.get('GroupSaveDataMap', {}).get('value', []):
        try:
            raw = g['value']['RawData']['value']
            gid = _norm(g.get('key', ''))
            base_ids = raw.get('base_ids', [])
            for bid in base_ids:
                bid_str = _norm(bid)
                if bid_str:
                    base_found = False
                    for b in wsd.get('BaseCampSaveData', {}).get('value', []):
                        try:
                            bgid = _norm(b['value']['RawData']['value'].get('group_id_belong_to', ''))
                            bkey = _norm(b.get('key', ''))
                            if bid_str == bkey and bgid != gid:
                                errors.append(f"Base {bid_str} belongs to guild {bgid} but guild {gid} lists it in base_ids")
                                base_found = True
                                break
                            if bid_str == bkey:
                                base_found = True
                                break
                        except Exception:
                            pass
                    if not base_found:
                        errors.append(f"Guild {gid} lists base {bid_str} in base_ids but no BaseCamp with that ID exists")
        except Exception:
            pass


def _check_map_object_container_ids(wsd: dict, container_ids: set, errors: list[str]) -> None:
    for mo in wsd.get('MapObjectSaveData', {}).get('value', []):
        try:
            modules = mo['value']['RawData']['value'].get('MapObjectModuleMap', {})
            if 'MapObjectModuleModule' in modules:
                module = modules['MapObjectModuleModule']
                if isinstance(module, dict) and isinstance(module.get('value'), list):
                    for entry in module['value']:
                        if isinstance(entry, dict):
                            for m_key, m_val in entry.items():
                                if isinstance(m_val, dict):
                                    target = m_val.get('target_container_id', {}).get('value', '')
                                    if target:
                                        norm_target = _norm(target)
                                        if norm_target not in container_ids:
                                            mo_id = _norm(mo.get('key', ''))
                                            errors.append(f"MapObject {mo_id} has target_container_id {target} which does not match any container")
        except Exception:
            pass


def _check_dynamic_item_links(wsd: dict, dynamic_ids: set, errors: list[str]) -> None:
    for cont in wsd.get('ItemContainerSaveData', {}).get('value', []):
        slots = cont.get('value', {}).get('Slots', {})
        if isinstance(slots, dict):
            raw_slots = slots.get('value', [])
            for slot in raw_slots:
                try:
                    raw = slot.get('RawData', {}).get('value', {})
                    local_id = raw.get('item', {}).get('dynamic_id', {}).get('local_id_in_created_world', {}).get('value', '')
                    if local_id and str(local_id) not in dynamic_ids:
                        errors.append(f"Slot references dynamic item {local_id} which is not registered in DynamicItemSaveData")
                except Exception:
                    pass
