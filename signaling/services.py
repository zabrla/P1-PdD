from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings

ROLE_INITIATOR = "initiator"
ROLE_RESPONDER = "responder"


class SignalingError(Exception):
    """Erro esperado de regra de negócio (mapeado para mensagem 'error' no WS)."""


@dataclass
class Peer:
    channel_name: str
    role: str
    joined_at: float = field(default_factory=time.time)
    validated: bool = False


@dataclass
class Room:
    name: str
    peers: dict[str, Peer] = field(default_factory=dict)  # channel_name -> Peer
    challenge: Optional[str] = None
    challenge_created_at: Optional[float] = None
    handshake_complete: bool = False

    def is_full(self) -> bool:
        return len(self.peers) >= settings.SIGNALING_ROOM_MAX_PEERS

    def other_peer(self, channel_name: str) -> Optional[Peer]:
        for cn, peer in self.peers.items():
            if cn != channel_name:
                return peer
        return None


class RoomManager:
    """Gerencia salas de sinalização (1 sala = no máximo 2 peers)."""

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._lock = threading.Lock()


    # ciclo de vida da sala / peers 

    def join(self, room_name: str, channel_name: str) -> tuple[Peer, Room]:
        """Adiciona um peer à sala, atribuindo o papel (role) dele."""

        with self._lock:
            room = self._rooms.setdefault(room_name, Room(name=room_name))

            if channel_name in room.peers:
                raise SignalingError("Você já está conectado nesta sala.")

            if room.is_full():
                raise SignalingError(
                    "Sala cheia: o handshake P2P é estritamente entre dois peers."
                )

            role = ROLE_INITIATOR if not room.peers else ROLE_RESPONDER
            peer = Peer(channel_name=channel_name, role=role)
            room.peers[channel_name] = peer
            return peer, room

    def leave(self, room_name: str, channel_name: str) -> Optional[Room]:
        with self._lock:
            room = self._rooms.get(room_name)

            if not room:
                return None

            room.peers.pop(channel_name, None)
            room.challenge = None
            room.challenge_created_at = None
            room.handshake_complete = False

            if not room.peers:
                del self._rooms[room_name]
                return None
            return room

    def get_room(self, room_name: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_name)

    # desafio de validação do handshake

    def issue_challenge(self, room_name: str) -> str:
        """Gera um token assinado (nonce + HMAC) para a sala quando ela atinge 2 peers."""

        with self._lock:
            room = self._rooms.get(room_name)
            if not room:
                raise SignalingError("Sala não encontrada.")

            nonce = secrets.token_hex(16)
            signature = self._sign(room_name, nonce)
            token = f"{nonce}.{signature}"

            room.challenge = token
            room.challenge_created_at = time.time()
            return token

    def verify_challenge(self, room_name: str, token: str) -> bool:

        with self._lock:
            room = self._rooms.get(room_name)
            if not room or not room.challenge:
                return False

            if room.challenge_created_at is not None:
                age = time.time() - room.challenge_created_at
                if age > settings.SIGNALING_CHALLENGE_TTL_SECONDS:
                    return False

            valid = hmac.compare_digest(room.challenge, token)
            if valid:
                room.handshake_complete = True
                for peer in room.peers.values():
                    peer.validated = True
            return valid

    @staticmethod
    def _sign(room_name: str, nonce: str) -> str:
        key = settings.SECRET_KEY.encode("utf-8")
        message = f"{room_name}:{nonce}".encode("utf-8")
        return hmac.new(key, message, hashlib.sha256).hexdigest()


# Instância única do processo, importada pelo consumer.
room_manager = RoomManager()
