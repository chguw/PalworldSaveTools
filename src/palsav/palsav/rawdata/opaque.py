from typing import Any
from palsav.archive import FArchiveReader, FArchiveWriter


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name == "StructProperty":
        return {
            "skip_type": type_name,
            "struct_type": reader.fstring(),
            "struct_id": reader.guid(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    elif type_name == "MapProperty":
        return {
            "skip_type": type_name,
            "key_type": reader.fstring(),
            "value_type": reader.fstring(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    elif type_name == "ArrayProperty":
        return {
            "skip_type": type_name,
            "array_type": reader.fstring(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    else:
        return {"skip_type": type_name, "value": reader.read(size)}


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type == "StructProperty":
        writer.fstring(properties["struct_type"])
        writer.guid(properties["struct_id"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "MapProperty":
        writer.fstring(properties["key_type"])
        writer.fstring(properties["value_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "ArrayProperty":
        writer.fstring(properties["array_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    else:
        writer.write(properties["value"])
        return len(properties["value"])
