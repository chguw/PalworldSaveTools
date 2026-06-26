from palworld_aio import constants
from palworld_aio.utils import fast_deepcopy


def verify_roundtrip(level_json: dict) -> list[str]:
    errors = []
    if level_json is None:
        errors.append('Cannot verify roundtrip: level_json is None')
        return errors
    if not constants.current_save_path:
        errors.append('Cannot verify roundtrip: no save path set')
        return errors
    try:
        from palworld_aio.utils import gvasfile_to_sav, sav_to_gvas_wrapper
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.sav', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            wrapper = level_json
            gvasfile_to_sav(wrapper.gvas_file, tmp_path)
            reloaded = sav_to_gvas_wrapper(tmp_path)
            original_wsd = wrapper['properties']['worldSaveData']['value']
            reloaded_wsd = reloaded['properties']['worldSaveData']['value']
            _compare_entity_counts(original_wsd, reloaded_wsd, errors)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as e:
        errors.append(f'Roundtrip verification failed: {e}')
    return errors


def _compare_entity_count(label: str, original: int | None, reloaded: int | None, errors: list[str]) -> None:
    if original != reloaded:
        errors.append(f'Roundtrip entity count mismatch: {label}: original={original}, reloaded={reloaded}')


def _compare_entity_counts(original: dict, reloaded: dict, errors: list[str]) -> None:
    entity_keys = [
        'CharacterSaveParameterMap',
        'GroupSaveDataMap',
        'ItemContainerSaveData',
        'BaseCampSaveData',
        'MapObjectSaveData',
        'CharacterContainerSaveData',
        'DynamicItemSaveData',
    ]
    for key in entity_keys:
        orig_val = original.get(key, {}).get('value')
        if key == 'DynamicItemSaveData' and isinstance(orig_val, dict):
            orig_val = orig_val.get('values')
        rel_val = reloaded.get(key, {}).get('value')
        if key == 'DynamicItemSaveData' and isinstance(rel_val, dict):
            rel_val = rel_val.get('values')
        orig_count = len(orig_val) if isinstance(orig_val, list) else None
        rel_count = len(rel_val) if isinstance(rel_val, list) else None
        _compare_entity_count(key, orig_count, rel_count, errors)


def verify_slice(wrapper, path_fn) -> list[str]:
    pass
