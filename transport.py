import json
import socket
import struct
from typing import Any, Dict, Optional
// yes

def _recv_exact(sock: socket.socket, length: int) -> Optional[bytes]:
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def send_frame(sock: socket.socket, obj: Dict[str, Any]) -> None:
    payload = json.dumps(obj).encode("utf-8")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def recv_frame(sock: socket.socket) -> Optional[Dict[str, Any]]:
    header = _recv_exact(sock, 4)
    if not header:
        return None

    (length,) = struct.unpack("!I", header)
    if length <= 0:
        return None

    payload = _recv_exact(sock, length)
    if payload is None:
        return None

    return json.loads(payload.decode("utf-8"))
