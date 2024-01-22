import asyncio
import unittest
from unittest.mock import MagicMock, patch
import aiosqlite

from server import Server
from client import Client


class TestServer(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    async def test_handle_send_command(self):
        server = Server()
        client = Client(None, None)
        client.nickname = 'Alice'
        client.send = MagicMock()

        await server.handle_send_command(client, ['Hello, everyone!'])

        client.send.assert_called_once_with('Alice: Hello, everyone!')

    async def test_handle_private_command(self):
        server = Server()
        alice = Client(None, None)
        bob = Client(None, None)
        bob.nickname = 'Bob'
        server.find_client_by_nickname = MagicMock(return_value=[bob])
        alice.send = MagicMock()
        bob.send = MagicMock()

        await server.handle_private_command(alice, ['Bob', 'Hello, Bob!'])

        alice.send.assert_called_once_with('Private message to Bob: Hello, Bob!')
        bob.send.assert_called_once_with('Private message from Alice: Hello, Bob!')


class TestClient(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    async def test_send(self):
        reader = MagicMock()
        writer = MagicMock()
        client = Client(reader, writer)

        await client.send('Hello!')

        writer.write.assert_called_once_with(b'Hello!\n')
        writer.drain.assert_awaited_once()

    async def test_add_warning(self):
        client = Client(None, None)
        client.nickname = 'Alice'
        client.warnings = 1

        with patch('aiosqlite.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_connect.return_value.__aenter__.return_value = mock_cursor
            mock_cursor.execute = MagicMock()

            await client.add_warning('Bob')

            mock_cursor.execute.assert_called_once_with(
                'INSERT INTO warnings (sender, receiver, timestamp) VALUES (?, ?, ?)',
                ('Bob', 'Alice', mock_connect.return_value.timestamp())
            )
            mock_connect.return_value.commit.assert_awaited_once()
            self.assertEqual(client.warnings, 2)


if __name__ == '__main__':
    unittest.main()
