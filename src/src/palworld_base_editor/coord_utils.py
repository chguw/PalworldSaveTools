import palworld_coord
def calculate_coordinate_offset(original_save_coords, new_map_coords, use_new_map=True):
    original_x, original_y, original_z = original_save_coords
    new_map_x, new_map_y = new_map_coords
    target_save_x, target_save_y = palworld_coord.map_to_sav(new_map_x, new_map_y, new=use_new_map)
    offset_x = target_save_x - original_x
    offset_y = target_save_y - original_y
    offset_z = 0
    return (offset_x, offset_y, offset_z)
def apply_offset_to_translation(translation, offset):
    if not isinstance(translation, dict):
        return translation
    result = translation.copy()
    result['x'] = translation.get('x', 0) + offset[0]
    result['y'] = translation.get('y', 0) + offset[1]
    result['z'] = translation.get('z', 0) + offset[2]
    return result
def save_coords_to_map(save_x, save_y, use_new=True):
    return palworld_coord.sav_to_map(save_x, save_y, new=use_new)
def map_coords_to_save(map_x, map_y, use_new=True):
    return palworld_coord.map_to_sav(map_x, map_y, new=use_new)
def get_base_spawn_translation(base_json_data):
    try:
        spawn_transform = base_json_data['base_camp']['value']['WorkerDirector']['value']['RawData']['value']['spawn_transform']
        return spawn_transform['translation']
    except (KeyError, TypeError):
        return None
def get_base_main_translation(base_json_data):
    try:
        transform = base_json_data['base_camp']['value']['RawData']['value']['transform']
        return transform['translation']
    except (KeyError, TypeError):
        return None