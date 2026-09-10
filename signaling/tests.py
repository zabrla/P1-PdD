from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from PdP.asgi import application
from .services import ROLE_INITIATOR, ROLE_RESPONDER


class SignalingConsumerTests(TransactionTestCase):

    async def test_peer_connects(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/signaling/test-room/",
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_two_peers_join_same_room(self):
        peer_a = WebsocketCommunicator(
            application,
            "/ws/signaling/test-room-two-peers/",
        )

        peer_b = WebsocketCommunicator(
            application,
            "/ws/signaling/test-room-two-peers/",
        )

        connected_a, _ = await peer_a.connect()
        connected_b, _ = await peer_b.connect()

        self.assertTrue(connected_a)
        self.assertTrue(connected_b)

        role_a = await peer_a.receive_json_from()
        role_b = await peer_b.receive_json_from()

        self.assertEqual(role_a["type"], "role")
        self.assertEqual(role_b["type"], "role")

        self.assertEqual(role_a["role"], ROLE_INITIATOR)
        self.assertEqual(role_b["role"], ROLE_RESPONDER)

        peer_joined = await peer_a.receive_json_from()

        self.assertEqual(
            peer_joined,
            {"type": "peer_joined"},
        )

        await peer_a.disconnect()
        await peer_b.disconnect()
