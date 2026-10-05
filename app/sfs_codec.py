from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any


SFS_NULL = 0
SFS_BOOL = 1
SFS_BYTE = 2
SFS_SHORT = 3
SFS_INT = 4
SFS_LONG = 5
SFS_FLOAT = 6
SFS_DOUBLE = 7
SFS_UTF_STRING = 8
SFS_BOOL_ARRAY = 9
SFS_BYTE_ARRAY = 10
SFS_SHORT_ARRAY = 11
SFS_INT_ARRAY = 12
SFS_LONG_ARRAY = 13
SFS_FLOAT_ARRAY = 14
SFS_DOUBLE_ARRAY = 15
SFS_UTF_STRING_ARRAY = 16
SFS_ARRAY = 17
SFS_OBJECT = 18
SFS_TEXT = 20


class SFSByte(int):
    pass


class SFSShort(int):
    pass


class SFSLong(int):
    pass


class SFSFloat(float):
    pass


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, size: int) -> bytes:
        chunk = self.data[self.pos : self.pos + size]
        if len(chunk) != size:
            raise ValueError(f"truncated SFS payload at {self.pos}: wanted {size}, got {len(chunk)}")
        self.pos += size
        return chunk

    def u8(self) -> int:
        return self.read(1)[0]

    def u16(self) -> int:
        return struct.unpack(">H", self.read(2))[0]

    def i32(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def utf(self) -> str:
        return self.read(self.u16()).decode("utf-8", "replace")


def _infer_type(value: Any) -> int:
    if value is None:
        return SFS_NULL
    if isinstance(value, bool):
        return SFS_BOOL
    if isinstance(value, SFSByte):
        return SFS_BYTE
    if isinstance(value, SFSShort):
        return SFS_SHORT
    if isinstance(value, SFSLong):
        return SFS_LONG
    if isinstance(value, SFSFloat):
        return SFS_FLOAT
    if isinstance(value, int):
        return SFS_INT if -(2**31) <= value <= 2**31 - 1 else SFS_LONG
    if isinstance(value, float):
        return SFS_DOUBLE
    if isinstance(value, str):
        return SFS_UTF_STRING if len(value.encode("utf-8")) <= 65535 else SFS_TEXT
    if isinstance(value, dict):
        return SFS_OBJECT
    if isinstance(value, (list, tuple)):
        return SFS_ARRAY
    if isinstance(value, (bytes, bytearray)):
        return SFS_BYTE_ARRAY
    raise TypeError(f"unsupported SFS value: {type(value)!r}")


def _encode_utf(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > 65535:
        raise ValueError("SFS UTF string is too long")
    return struct.pack(">H", len(raw)) + raw


def _encode_value(type_id: int, value: Any) -> bytes:
    if type_id == SFS_NULL:
        return b""
    if type_id == SFS_BOOL:
        return struct.pack(">B", 1 if value else 0)
    if type_id == SFS_BYTE:
        return struct.pack(">b", int(value))
    if type_id == SFS_SHORT:
        return struct.pack(">h", int(value))
    if type_id == SFS_INT:
        return struct.pack(">i", int(value))
    if type_id == SFS_LONG:
        return struct.pack(">q", int(value))
    if type_id == SFS_FLOAT:
        return struct.pack(">f", float(value))
    if type_id == SFS_DOUBLE:
        return struct.pack(">d", float(value))
    if type_id == SFS_UTF_STRING:
        return _encode_utf(str(value))
    if type_id == SFS_TEXT:
        raw = str(value).encode("utf-8")
        return struct.pack(">i", len(raw)) + raw
    if type_id == SFS_BYTE_ARRAY:
        raw = bytes(value)
        return struct.pack(">i", len(raw)) + raw
    if type_id == SFS_ARRAY:
        parts = [struct.pack(">H", len(value))]
        for item in value:
            item_type = _infer_type(item)
            parts.append(struct.pack(">B", item_type))
            parts.append(_encode_value(item_type, item))
        return b"".join(parts)
    if type_id == SFS_OBJECT:
        return _encode_object_body(value)
    raise TypeError(f"encoding for SFS type {type_id} is not implemented")


def _encode_object_body(value: dict[str, Any]) -> bytes:
    parts = [struct.pack(">H", len(value))]
    for key, item in value.items():
        type_id = _infer_type(item)
        parts.append(_encode_utf(str(key)))
        parts.append(struct.pack(">B", type_id))
        parts.append(_encode_value(type_id, item))
    return b"".join(parts)


def encode_sfs_object(value: dict[str, Any]) -> bytes:
    return struct.pack(">B", SFS_OBJECT) + _encode_object_body(value)


def _decode_value(reader: _Reader, type_id: int) -> Any:
    if type_id == SFS_NULL:
        return None
    if type_id == SFS_BOOL:
        return reader.u8() != 0
    if type_id == SFS_BYTE:
        return struct.unpack(">b", reader.read(1))[0]
    if type_id == SFS_SHORT:
        return struct.unpack(">h", reader.read(2))[0]
    if type_id == SFS_INT:
        return struct.unpack(">i", reader.read(4))[0]
    if type_id == SFS_LONG:
        return struct.unpack(">q", reader.read(8))[0]
    if type_id == SFS_FLOAT:
        return struct.unpack(">f", reader.read(4))[0]
    if type_id == SFS_DOUBLE:
        return struct.unpack(">d", reader.read(8))[0]
    if type_id == SFS_UTF_STRING:
        return reader.utf()
    if type_id == SFS_TEXT:
        return reader.read(reader.i32()).decode("utf-8", "replace")
    if type_id == SFS_BOOL_ARRAY:
        return [reader.u8() != 0 for _ in range(reader.u16())]
    if type_id == SFS_BYTE_ARRAY:
        return reader.read(reader.i32())
    if type_id == SFS_SHORT_ARRAY:
        return [struct.unpack(">h", reader.read(2))[0] for _ in range(reader.u16())]
    if type_id == SFS_INT_ARRAY:
        return [struct.unpack(">i", reader.read(4))[0] for _ in range(reader.u16())]
    if type_id == SFS_LONG_ARRAY:
        return [struct.unpack(">q", reader.read(8))[0] for _ in range(reader.u16())]
    if type_id == SFS_FLOAT_ARRAY:
        return [struct.unpack(">f", reader.read(4))[0] for _ in range(reader.u16())]
    if type_id == SFS_DOUBLE_ARRAY:
        return [struct.unpack(">d", reader.read(8))[0] for _ in range(reader.u16())]
    if type_id == SFS_UTF_STRING_ARRAY:
        return [reader.utf() for _ in range(reader.u16())]
    if type_id == SFS_ARRAY:
        values = []
        for _ in range(reader.u16()):
            values.append(_decode_value(reader, reader.u8()))
        return values
    if type_id == SFS_OBJECT:
        return _decode_object_body(reader)
    raise TypeError(f"unknown SFS type id: {type_id}")


def _decode_object_body(reader: _Reader) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for _ in range(reader.u16()):
        key = reader.utf()
        result[key] = _decode_value(reader, reader.u8())
    return result


def decode_sfs_object(data: bytes) -> dict[str, Any]:
    reader = _Reader(data)
    root_type = reader.u8()
    if root_type != SFS_OBJECT:
        raise ValueError(f"expected SFS object root ({SFS_OBJECT}), got {root_type}")
    return _decode_object_body(reader)


@dataclass(slots=True)
class ClientFrame:
    request_id: int
    command: str
    params: dict[str, Any]


@dataclass(slots=True)
class ServerFrame:
    command: str
    payload: dict[str, Any]


def parse_client_frame(data: bytes) -> ClientFrame:
    if len(data) < 10:
        raise ValueError("client frame is too short")
    if data[0] != 0:
        raise ValueError(f"unsupported client frame marker: {data[0]}")

    request_id = struct.unpack(">q", data[1:9])[0]
    command_length = data[9]
    command_end = 10 + command_length
    if command_length == 0 or command_end > len(data):
        raise ValueError("invalid command length")

    command = data[10:command_end].decode("ascii", "replace")
    payload_raw = data[command_end:]
    params = decode_sfs_object(payload_raw) if payload_raw else {}
    if isinstance(params.get("data"), dict):
        params = params["data"]
    return ClientFrame(request_id=request_id, command=command, params=params)


def build_client_frame(request_id: int, command: str, params: dict[str, Any] | None = None) -> bytes:
    command_raw = command.encode("ascii")
    if len(command_raw) > 255:
        raise ValueError("command is too long")
    payload = encode_sfs_object({"data": params or {}})
    return (
        b"\x00"
        + struct.pack(">q", request_id)
        + struct.pack(">B", len(command_raw))
        + command_raw
        + payload
    )


def build_server_frame(command: str, payload: dict[str, Any] | None = None) -> bytes:
    command_raw = command.encode("ascii")
    return struct.pack(">H", len(command_raw)) + command_raw + encode_sfs_object(payload or {})


def parse_server_frame(data: bytes) -> ServerFrame:
    if len(data) < 3:
        raise ValueError("server frame is too short")
    command_length = struct.unpack(">H", data[:2])[0]
    command_end = 2 + command_length
    if command_length == 0 or command_end > len(data):
        raise ValueError("invalid server command length")
    command = data[2:command_end].decode("ascii", "replace")
    payload = decode_sfs_object(data[command_end:]) if command_end < len(data) else {}
    return ServerFrame(command=command, payload=payload)
