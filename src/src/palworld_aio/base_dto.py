from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, computed_field
class BaseDTO(BaseModel):
    id: UUID
    name: Optional[str] = None
    storage_containers: Dict[UUID, Dict[str, Any]] = Field(default_factory=dict)
    location: Optional[Dict[str, float]] = None
    area_range: Optional[float] = None
class ContainerDTO(BaseModel):
    id: UUID
    name: str
    type: str
    slot_count: int
    location: str
    map_object_id: str
    is_guild_chest: bool = False
def get_base_containers_simple(base_id: UUID) -> List[ContainerDTO]:
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    containers = []
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objs:
        map_object_id = obj.get('MapObjectId', {}).get('value', '')
        if not map_object_id:
            continue
        is_container = any((container_type in map_object_id for container_type in ['ItemChest', 'StorageBox', 'ItemBox', 'ItemContainer']))
        if not is_container:
            continue
        raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        base_camp_id = raw_data.get('base_camp_id_belong_to')
        if not base_camp_id or str(base_camp_id).replace('-', '').lower() != base_id_low:
            continue
        module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
        container_id = None
        for module in module_map:
            if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                container_id = module_raw.get('target_container_id')
                break
        if not container_id:
            continue
        container_type = 'Unknown'
        container_name = 'Unknown Container'
        if 'ItemChest' in map_object_id:
            container_type = 'ItemChest'
            container_name = 'Chest'
        elif 'StorageBox' in map_object_id:
            container_type = 'StorageBox'
            container_name = 'Storage Box'
        elif 'ItemBox' in map_object_id:
            container_type = 'ItemBox'
            container_name = 'Item Box'
        elif 'ItemContainer' in map_object_id:
            container_type = 'ItemContainer'
            container_name = 'Container'
        slot_count = get_container_slot_count(str(container_id))
        location = get_container_location(obj)
        containers.append(ContainerDTO(id=UUID(str(container_id)), name=container_name, type=container_type, slot_count=slot_count, location=location, map_object_id=map_object_id, is_guild_chest=False))
    guild_chest = get_guild_chest_for_base(base_id)
    if guild_chest:
        containers.append(guild_chest)
    return containers
def get_container_slot_count(container_id: str) -> int:
    try:
        from palworld_aio import constants
    except ImportError:
        from . import constants
    if not constants.loaded_level_json:
        return 0
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            return cont['value'].get('SlotNum', {}).get('value', 0)
        except:
            pass
    return 0
def get_container_location(map_obj) -> str:
    try:
        transform = map_obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('transform', {})
        if transform and 'translation' in transform:
            trans = transform['translation']
            try:
                from palworld_coord import sav_to_map
                coords = sav_to_map(trans['x'], trans['y'], new=True)
                return f'X: {coords[0]:.1f}, Y: {coords[1]:.1f}'
            except ImportError:
                return f"X: {trans['x']:.1f}, Y: {trans['y']:.1f}"
    except:
        pass
    return 'Unknown Location'
def get_guild_chest_for_base(base_id: UUID) -> Optional[ContainerDTO]:
    try:
        from palworld_aio import constants
    except ImportError:
        from . import constants
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    guild_id = None
    for base in base_list:
        if str(base['key']).replace('-', '').lower() == base_id_low:
            guild_id = base['value']['RawData']['value'].get('group_id_belong_to')
            break
    if not guild_id:
        return None
    guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
    guild_id_str = str(guild_id)
    guild_id_low = guild_id_str.replace('-', '').lower()
    for guild_entry in guild_extra_map:
        try:
            guild_key = str(guild_entry.get('key', '')).replace('-', '').lower()
            if guild_key == guild_id_low:
                guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
                raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
                container_id = raw_data.get('container_id')
                if container_id:
                    slot_count = get_container_slot_count(str(container_id))
                    return ContainerDTO(id=UUID(str(container_id)), name='Guild Chest', type='GuildChest', slot_count=slot_count, location='Guild Storage', map_object_id='GuildChest', is_guild_chest=True)
        except:
            continue
    return None