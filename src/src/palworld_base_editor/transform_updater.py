import copy
def _deep_update_translation(obj, path, offset, stats=None):
    if stats is None:
        stats = {'updated': 0, 'skipped': 0}
    if not isinstance(obj, dict):
        return obj
    current = obj
    for i, key in enumerate(path[:-1]):
        if key not in current:
            return obj
        current = current[key]
    final_key = path[-1]
    if final_key in current and isinstance(current[final_key], dict):
        if 'x' in current[final_key] and 'y' in current[final_key]:
            current[final_key]['x'] += offset[0]
            current[final_key]['y'] += offset[1]
            if 'z' in current[final_key]:
                current[final_key]['z'] += offset[2]
            stats['updated'] += 1
    return obj
def update_base_transforms(base_json_data, offset):
    if not isinstance(base_json_data, dict):
        return (base_json_data, {'updated': 0, 'skipped': 0})
    try:
        result = copy.deepcopy(base_json_data)
    except:
        result = dict(base_json_data)
    stats = {'updated': 0, 'skipped': 0, 'details': []}
    try:
        spawn_t = result['base_camp']['value']['WorkerDirector']['value']['RawData']['value']['spawn_transform']['translation']
        spawn_t['x'] += offset[0]
        spawn_t['y'] += offset[1]
        spawn_t['z'] += offset[2]
        stats['updated'] += 1
        stats['details'].append('WorkerDirector spawn_transform')
    except (KeyError, TypeError):
        stats['skipped'] += 1
    try:
        main_t = result['base_camp']['value']['RawData']['value']['transform']['translation']
        main_t['x'] += offset[0]
        main_t['y'] += offset[1]
        main_t['z'] += offset[2]
        stats['updated'] += 1
        stats['details'].append('BaseCamp transform')
    except (KeyError, TypeError):
        stats['skipped'] += 1
    try:
        fast_travel_t = result['base_camp']['value']['RawData']['value']['fast_travel_local_transform']['translation']
        fast_travel_t['x'] += offset[0]
        fast_travel_t['y'] += offset[1]
        fast_travel_t['z'] += offset[2]
        stats['updated'] += 1
        stats['details'].append('Fast travel transform')
    except (KeyError, TypeError):
        pass
    map_objects = result.get('map_objects', [])
    if isinstance(map_objects, list):
        for i, obj in enumerate(map_objects):
            try:
                model_raw = obj['Model']['value']['RawData']['value']
                if 'initital_transform_cache' in model_raw:
                    t = model_raw['initital_transform_cache'].get('translation', {})
                    if isinstance(t, dict) and 'x' in t:
                        t['x'] += offset[0]
                        t['y'] += offset[1]
                        t['z'] += offset[2]
                        stats['updated'] += 1
            except (KeyError, TypeError):
                pass
    works = result.get('works', [])
    if isinstance(works, list):
        for i, work in enumerate(works):
            try:
                work_raw = work.get('RawData', {}).get('value', {})
                if 'transform' in work_raw:
                    t = work_raw['transform'].get('translation', {})
                    if isinstance(t, dict) and 'x' in t:
                        t['x'] += offset[0]
                        t['y'] += offset[1]
                        t['z'] += offset[2]
                        stats['updated'] += 1
            except (KeyError, TypeError):
                pass
    return (result, stats)
def get_transform_summary(base_json_data):
    summary = {'spawn_transform': None, 'main_transform': None, 'map_object_count': 0, 'work_count': 0}
    try:
        t = base_json_data['base_camp']['value']['WorkerDirector']['value']['RawData']['value']['spawn_transform']['translation']
        summary['spawn_transform'] = (t.get('x', 0), t.get('y', 0), t.get('z', 0))
    except (KeyError, TypeError):
        pass
    try:
        t = base_json_data['base_camp']['value']['RawData']['value']['transform']['translation']
        summary['main_transform'] = (t.get('x', 0), t.get('y', 0), t.get('z', 0))
    except (KeyError, TypeError):
        pass
    summary['map_object_count'] = len(base_json_data.get('map_objects', []))
    summary['work_count'] = len(base_json_data.get('works', []))
    return summary