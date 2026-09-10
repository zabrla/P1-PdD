
from __future__ import annotations
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from .services import ROLE_INITIATOR, SignalingError, room_manager

logger = logging.getLogger(__name__)
RELAYED_MESSAGE_TYPES = {"offer", "answer", "ice_candidate"}


class SignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.group_name = f"signaling_{self.room_name}"

        try:
            peer, room = await self._join_room()
        except SignalingError as exc:
            await self.accept()
            await self._send_json({"type": "error", "message": str(exc)})
            await self.close(code=4000)
            return

        self.role = peer.role

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self._send_json({"type": "role", "role": self.role})

        if len(room.peers) == 2:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "peer.joined", "sender_channel": self.channel_name},
            )
            await self._issue_challenge_to_initiator()

    async def disconnect(self, close_code):
        room = await self._leave_room()
        if room is not None:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "peer.left", "sender_channel": self.channel_name},
            )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_json({"type": "error", "message": "JSON inválido."})
            return

        msg_type = data.get("type")

        if msg_type in RELAYED_MESSAGE_TYPES:
            await self._relay(msg_type, data)
        elif msg_type == "challenge_response":
            await self._handle_challenge_response(data)
        elif msg_type == "ping":
            await self._send_json({"type": "pong"})
        else:
            await self._send_json(
                {"type": "error", "message": f"Tipo de mensagem desconhecido: {msg_type!r}"}
            )

    # handlers de grupo (channel layer)

    async def peer_joined(self, event):
        if event["sender_channel"] == self.channel_name:
            return
        await self._send_json({"type": "peer_joined"})

    async def peer_left(self, event):
        if event["sender_channel"] == self.channel_name:
            return
        await self._send_json({"type": "peer_left"})

    async def signal_relay(self, event):
        if event["sender_channel"] == self.channel_name:
            return
        await self._send_json(event["payload"])

    async def handshake_complete(self, event):
        await self._send_json({"type": "handshake_complete"})

    # helpers

    async def _relay(self, msg_type: str, data: dict):

        """Repassa offer/answer/ice_candidate para o outro peer da sala,
        sem inspecionar o conteúdo (o SDP/ICE é responsabilidade do WebRTC).
        """

        payload = {"type": msg_type}
        if "sdp" in data:
            payload["sdp"] = data["sdp"]
        if "candidate" in data:
            payload["candidate"] = data["candidate"]

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "signal.relay",
                "sender_channel": self.channel_name,
                "payload": payload,
            },
        )

    async def _issue_challenge_to_initiator(self):
        from asgiref.sync import sync_to_async

        token = await sync_to_async(room_manager.issue_challenge)(self.room_name)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "challenge.issued",
                "sender_channel": self.channel_name,
                "token": token,
            },
        )

    async def challenge_issued(self, event):
        if getattr(self, "role", None) == ROLE_INITIATOR:
            await self._send_json({"type": "challenge", "token": event["token"]})

    async def _handle_challenge_response(self, data: dict):
        from asgiref.sync import sync_to_async

        token = data.get("token", "")
        valid = await sync_to_async(room_manager.verify_challenge)(self.room_name, token)

        if valid:
            await self.channel_layer.group_send(
                self.group_name, {"type": "handshake.complete"}
            )
        else:
            await self._send_json(
                {"type": "error", "message": "Falha na validação do handshake P2P (token inválido ou expirado)."}
            )

    async def _join_room(self):
        from asgiref.sync import sync_to_async

        return await sync_to_async(room_manager.join)(self.room_name, self.channel_name)

    async def _leave_room(self):
        from asgiref.sync import sync_to_async

        return await sync_to_async(room_manager.leave)(self.room_name, self.channel_name)

    async def _send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))
