import base64
from typing import Any, Callable
from loguru import logger
from palworld_save_tools.archive import FArchiveReader, FArchiveWriter
def custom_version_reader(reader: FArchiveReader):
    return (reader.guid(), reader.i32())
def custom_version_writer(writer: FArchiveWriter, value: tuple[str, int]):
    writer.guid(value[0])
    writer.i32(value[1])
class GvasHeader:
    magic: int
    save_game_version: int
    package_file_version_ue4: int
    package_file_version_ue5: int
    engine_version_major: int
    engine_version_minor: int
    engine_version_patch: int
    engine_version_changelist: int
    engine_version_branch: str
    custom_version_format: int
    custom_versions: list[tuple[str, int]]
    save_game_class_name: str
    @staticmethod
    def read(reader: FArchiveReader) -> 'GvasHeader':
        header = GvasHeader()
        header.magic = reader.i32()
        if header.magic != 1396790855:
            raise Exception('invalid magic')
        header.save_game_version = reader.i32()
        if header.save_game_version != 3:
            raise Exception(f'expected save game version 3, got {header.save_game_version}')
        header.package_file_version_ue4 = reader.i32()
        header.package_file_version_ue5 = reader.i32()
        header.engine_version_major = reader.u16()
        header.engine_version_minor = reader.u16()
        header.engine_version_patch = reader.u16()
        header.engine_version_changelist = reader.u32()
        header.engine_version_branch = reader.fstring()
        header.custom_version_format = reader.i32()
        if header.custom_version_format != 3:
            raise Exception(f'expected custom version format 3, got {header.custom_version_format}')
        header.custom_versions = reader.tarray(custom_version_reader)
        header.save_game_class_name = reader.fstring()
        return header
    @staticmethod
    def load(dict: dict[str, Any]) -> 'GvasHeader':
        header = GvasHeader()
        header.magic = dict['magic']
        header.save_game_version = dict['save_game_version']
        header.package_file_version_ue4 = dict['package_file_version_ue4']
        header.package_file_version_ue5 = dict['package_file_version_ue5']
        header.engine_version_major = dict['engine_version_major']
        header.engine_version_minor = dict['engine_version_minor']
        header.engine_version_patch = dict['engine_version_patch']
        header.engine_version_changelist = dict['engine_version_changelist']
        header.engine_version_branch = dict['engine_version_branch']
        header.custom_version_format = dict['custom_version_format']
        header.custom_versions = dict['custom_versions']
        header.save_game_class_name = dict['save_game_class_name']
        return header
    def dump(self) -> dict[str, Any]:
        return {'magic': self.magic, 'save_game_version': self.save_game_version, 'package_file_version_ue4': self.package_file_version_ue4, 'package_file_version_ue5': self.package_file_version_ue5, 'engine_version_major': self.engine_version_major, 'engine_version_minor': self.engine_version_minor, 'engine_version_patch': self.engine_version_patch, 'engine_version_changelist': self.engine_version_changelist, 'engine_version_branch': self.engine_version_branch, 'custom_version_format': self.custom_version_format, 'custom_versions': self.custom_versions, 'save_game_class_name': self.save_game_class_name}
    def write(self, writer: FArchiveWriter):
        writer.i32(self.magic)
        writer.i32(self.save_game_version)
        writer.i32(self.package_file_version_ue4)
        writer.i32(self.package_file_version_ue5)
        writer.u16(self.engine_version_major)
        writer.u16(self.engine_version_minor)
        writer.u16(self.engine_version_patch)
        writer.u32(self.engine_version_changelist)
        writer.fstring(self.engine_version_branch)
        writer.i32(self.custom_version_format)
        writer.tarray(custom_version_writer, self.custom_versions)
        writer.fstring(self.save_game_class_name)
class GvasFile:
    header: GvasHeader
    properties: dict[str, Any]
    trailer: bytes
    @staticmethod
    def read(data: bytes, type_hints: dict[str, str]={}, custom_properties: dict[str, tuple[Callable, Callable]]={}, allow_nan: bool=True) -> 'GvasFile':
        gvas_file = GvasFile()
        with FArchiveReader(data, type_hints=type_hints, custom_properties=custom_properties, allow_nan=allow_nan) as reader:
            gvas_file.header = GvasHeader.read(reader)
            gvas_file.properties = reader.properties_until_end()
            gvas_file.trailer = reader.read_to_end()
            if gvas_file.trailer != b'\x00\x00\x00\x00':
                logger.debug(f'{len(gvas_file.trailer)} bytes of trailer data, file may not have fully parsed')
        _enrich_guild_player_uids(gvas_file.properties)
        return gvas_file
    @staticmethod
    def load(dict: dict[str, Any]) -> 'GvasFile':
        gvas_file = GvasFile()
        gvas_file.header = GvasHeader.load(dict['header'])
        gvas_file.properties = dict['properties']
        gvas_file.trailer = base64.b64decode(dict['trailer'])
        return gvas_file
    def dump(self) -> dict[str, Any]:
        return {'header': self.header.dump(), 'properties': self.properties, 'trailer': base64.b64encode(self.trailer).decode('utf-8')}
    def write(self, custom_properties: dict[str, tuple[Callable, Callable]]={}) -> bytes:
        writer = FArchiveWriter(custom_properties)
        self.header.write(writer)
        writer.properties(self.properties)
        writer.write(self.trailer)
        return writer.bytes()

def _enrich_guild_player_uids(properties: dict[str, Any]) -> None:
    wsd = properties.get('worldSaveData', {}).get('value')
    if not wsd:
        return
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    gsm = wsd.get('GroupSaveDataMap', {}).get('value', [])
    if not char_map or not gsm:
        return
    name_to_uid = {}
    for entry in char_map:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value', False):
                continue
            key = entry.get('key', {})
            uid_obj = key.get('PlayerUId', {})
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
            if not uid:
                continue
            nick = sp_val.get('NickName', {}).get('value', '')
            name = nick if nick else sp_val.get('CharacterID', {}).get('value', '')
            if name and name not in name_to_uid:
                name_to_uid[name] = uid
        except Exception:
            continue
    if not name_to_uid:
        return
    for g in gsm:
        players = g.get('value', {}).get('RawData', {}).get('value', {}).get('players', [])
        for player in players:
            uid = player.get('player_uid', '')
            if not uid or (isinstance(uid, str) and not uid.strip()):
                pname = player.get('player_info', {}).get('player_name', '')
                if pname:
                    direct = name_to_uid.get(pname)
                    if direct:
                        player['player_uid'] = direct
                    else:
                        for alt_name, alt_uid in name_to_uid.items():
                            if pname.lower() == alt_name.lower():
                                player['player_uid'] = alt_uid
                                break