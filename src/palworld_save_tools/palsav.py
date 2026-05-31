import logging
from palworld_save_tools.compressor import Compressor
from palworld_save_tools.compressor.oozlib import OozLib
from palworld_save_tools.compressor.zlib import Zlib
from palworld_save_tools.compressor.enums import SaveType
logger = logging.getLogger(__name__)
compressor = Compressor()
oozlib = OozLib()
z_lib = Zlib()
def configure_logging(debug: bool=False):
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'))
        root.addHandler(handler)
def decompress_sav_to_gvas(data: bytes, debug: bool=False) -> tuple[bytes, int]:
    configure_logging(debug)
    format = compressor.check_sav_format(data)
    if format is None:
        raise Exception('Unknown save format')
    match format:
        case SaveType.PLZ | SaveType.CNK:
            return z_lib.decompress(data)
        case SaveType.PLM:
            return oozlib.decompress(data)
        case _:
            raise Exception('Unknown save format')
def compress_gvas_to_sav(data: bytes, save_type: int, debug: bool=False) -> bytes:
    configure_logging(debug)
    format = compressor.check_savtype_format(save_type)
    if format is None:
        raise Exception('Unknown save type format')
    match format:
        case SaveType.PLZ | SaveType.CNK:
            return z_lib.compress(data, save_type)
        case SaveType.PLM:
            return oozlib.compress(data, save_type)