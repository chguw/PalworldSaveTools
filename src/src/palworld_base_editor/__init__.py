def get_base_editor_dialog():
    from .base_editor import BaseEditorDialog
    return BaseEditorDialog
def get_coord_utils():
    from .coord_utils import calculate_coordinate_offset, apply_offset_to_translation, save_coords_to_map, map_coords_to_save, get_base_spawn_translation, get_base_main_translation
    return {'calculate_coordinate_offset': calculate_coordinate_offset, 'apply_offset_to_translation': apply_offset_to_translation, 'save_coords_to_map': save_coords_to_map, 'map_coords_to_save': map_coords_to_save, 'get_base_spawn_translation': get_base_spawn_translation, 'get_base_main_translation': get_base_main_translation}
def get_transform_updater():
    from .transform_updater import update_base_transforms, get_transform_summary
    return {'update_base_transforms': update_base_transforms, 'get_transform_summary': get_transform_summary}
BaseEditorDialog = None
def __getattr__(name):
    global BaseEditorDialog
    if name == 'BaseEditorDialog':
        if BaseEditorDialog is None:
            from .base_editor import BaseEditorDialog as _BED
            BaseEditorDialog = _BED
        return BaseEditorDialog
    elif name == 'calculate_coordinate_offset':
        return get_coord_utils()['calculate_coordinate_offset']
    elif name == 'apply_offset_to_translation':
        return get_coord_utils()['apply_offset_to_translation']
    elif name == 'update_base_transforms':
        return get_transform_updater()['update_base_transforms']
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')