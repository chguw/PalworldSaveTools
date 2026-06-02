import logging
from palworld_save_tools import setup_logging
from palworld_save_tools.compressor import Compressor
from palworld_save_tools.compressor.oozlib import OozLib
from palworld_save_tools.compressor.zlib import Zlib
from palworld_save_tools.compressor.enums import SaveType
logger = logging.getLogger(__name__)
compressor = Compressor()
oozlib = OozLib()
z_lib = Zlib()
def decompress_sav_to_gvas(data: bytes, debug: bool=False) -> tuple[bytes, int]:
    setup_logging(debug=debug, quiet=True)
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
    setup_logging(debug=debug, quiet=True)
    format = compressor.check_savtype_format(save_type)
    if format is None:
        raise Exception('Unknown save type format')
    match format:
        case SaveType.PLZ | SaveType.CNK:
            return z_lib.compress(data, save_type)
        case SaveType.PLM:
            return oozlib.compress(data, save_type)