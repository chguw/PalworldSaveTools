from typing import Literal
from palworld_aio import constants
from palworld_aio.utils import fast_deepcopy
from palworld_aio.validation.schema_validator import validate_schema
from palworld_aio.validation.relation_auditor import audit_relations
from palworld_aio.validation.roundtrip_verifier import verify_roundtrip

ValidationLevel = Literal['schema', 'relation', 'full']


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        msg = 'Validation failed:\n' + '\n'.join(f'  - {e}' for e in errors)
        super().__init__(msg)


def snapshot() -> None:
    if constants.loaded_level_json is not None:
        constants.original_loaded_level_json = fast_deepcopy(constants.loaded_level_json)


def rollback() -> bool:
    if constants.original_loaded_level_json is not None and constants.loaded_level_json is not None:
        constants.loaded_level_json = fast_deepcopy(constants.original_loaded_level_json)
        constants.invalidate_container_lookup()
        return True
    return False


def validate(level_json: dict | None = None, level: ValidationLevel = 'relation') -> tuple[bool, list[str]]:
    if level_json is None:
        level_json = constants.loaded_level_json
    errors: list[str] = []
    if level_json is None:
        return False, ['loaded_level_json is None — nothing to validate']
    if level in ('schema', 'full'):
        errors.extend(validate_schema(level_json))
        if errors:
            return False, errors
    if level in ('relation', 'full'):
        errors.extend(audit_relations(level_json))
    if level == 'full':
        rt_errors = verify_roundtrip(level_json)
        errors.extend(rt_errors)
    return len(errors) == 0, errors


def validate_and_save(wrapper, path: str, level: ValidationLevel = 'relation') -> None:
    ok, errors = validate(wrapper, level)
    if not ok:
        rollback()
        raise ValidationError(errors)
    from palworld_aio.utils import gvasfile_to_sav
    gvasfile_to_sav(wrapper.gvas_file, path)
