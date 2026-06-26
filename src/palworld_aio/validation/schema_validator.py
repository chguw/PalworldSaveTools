import uuid

REQUIRED_PROPERTIES = ('header', 'trailer')
REQUIRED_WSD_ARRAYS = (
    'CharacterSaveParameterMap',
    'GroupSaveDataMap',
    'ItemContainerSaveData',
    'BaseCampSaveData',
    'MapObjectSaveData',
    'CharacterContainerSaveData',
)
OPTIONAL_ARRAYS = (
    'DynamicItemSaveData',
    'GuildExtraSaveDataMap',
    'WorkSaveData',
)


def validate_schema(level_json: dict) -> list[str]:
    errors = []
    if level_json is None:
        errors.append('loaded_level_json is None')
        return errors
    for key in REQUIRED_PROPERTIES:
        if key not in level_json:
            errors.append(f"Missing top-level key: '{key}'")
    props = level_json.get('properties')
    if props is None:
        errors.append("Missing 'properties' key")
        return errors
    wsd = props.get('worldSaveData', {}).get('value')
    if wsd is None:
        errors.append("worldSaveData.value is None or missing")
        return errors
    for arr_name in REQUIRED_WSD_ARRAYS:
        arr = wsd.get(arr_name, {}).get('value')
        if arr is None:
            errors.append(f"worldSaveData.{arr_name}.value is None")
            continue
        if not isinstance(arr, list):
            errors.append(f"worldSaveData.{arr_name}.value is not a list")
            continue
        for i, entry in enumerate(arr):
            if entry is None:
                errors.append(f"Null entry at worldSaveData.{arr_name}[{i}]")
            elif not isinstance(entry, dict):
                errors.append(f"Non-dict entry at worldSaveData.{arr_name}[{i}]: {type(entry).__name__}")
            elif 'key' not in entry:
                errors.append(f"Missing 'key' at worldSaveData.{arr_name}[{i}]")
            elif 'value' not in entry:
                errors.append(f"Missing 'value' at worldSaveData.{arr_name}[{i}]")
            else:
                _check_key_type(arr_name, i, entry['key'], errors)
    for arr_name in OPTIONAL_ARRAYS:
        arr = wsd.get(arr_name, {}).get('value')
        if arr is not None:
            if arr_name == 'DynamicItemSaveData':
                if not isinstance(arr, dict) or not isinstance(arr.get('values'), list):
                    errors.append(f"worldSaveData.{arr_name}.value is not a dict with 'values' list (type={type(arr).__name__})")
            elif not isinstance(arr, list):
                errors.append(f"worldSaveData.{arr_name}.value is not a list (type={type(arr).__name__})")
    return errors


def _check_key_type(arr_name: str, index: int, key, errors: list[str]) -> None:
    if not isinstance(key, dict):
        return
    for k, v in key.items():
        if isinstance(v, dict):
            val = v.get('value')
            if isinstance(val, str) and _looks_like_uuid(val) and not _is_valid_uuid(val):
                errors.append(f"worldSaveData.{arr_name}[{index}].key.{k}.value='{val}' is not a valid UUID")


def _looks_like_uuid(s: str) -> bool:
    cleaned = s.replace('-', '').lower()
    return len(cleaned) == 32 and all(c in '0123456789abcdef' for c in cleaned)


def _is_valid_uuid(s: str) -> bool:
    try:
        uuid.UUID(hex=s.replace('-', '').lower())
        return True
    except (ValueError, AttributeError):
        return False
