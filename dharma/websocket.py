# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import base64
import email.message
import email.parser
import hashlib
import logging
import socket
import struct
import sys
import json

try:
    # python 3
    from socketserver import BaseRequestHandler, TCPServer, ThreadingMixIn
except ImportError:
    # python 2
    from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn


class BaseWebSocketHandler(BaseRequestHandler):
    """Base class for WebSocket server."""

    REQUEST_TIMEOUT = 0.01
    _OPCODES = {
        0: 'continue',
        1: 'text',
        2: 'binary',
        8: 'close',
        9: 'ping',
        10: 'pong'
    }

    def handle(self):
        self.request.settimeout(self.REQUEST_TIMEOUT)
        str_t = str if sys.version_info[0] == 3 else lambda a, b: str(a).encode(b)
        while not self.should_close():
            try:
                request, headers = str_t(self.request.recv(1024), 'ascii').split('\r\n', 1)
                break
            except socket.timeout:
                #time.sleep(0.01)
                #print 'timeout 29'
                continue
        headers = email.parser.HeaderParser().parsestr(headers)
        # TODO(jschwartzentruber): validate request/headers
        hresponse = hashlib.sha1(headers['sec-websocket-key'].encode('ascii'))
        hresponse.update(b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
        resp = email.message.Message()
        resp.add_header('Upgrade', 'websocket')
        resp.add_header('Connection', 'Upgrade')
        resp.add_header('Sec-WebSocket-Accept', str_t(base64.b64encode(hresponse.digest()), 'ascii'))
        resp = resp.as_string(unixfrom=False).replace('\n', '\r\n')
        self.request.sendall('HTTP/1.1 101 Switching Protocols\r\n{}'.format(resp).encode('ascii'))
        self.open()
        buf = None
        buf_op = None
        try:
            while not self.should_close():
                try:
                    data = struct.unpack('BB', self.request.recv(2))
                except socket.timeout:
                    # no data
                    #time.sleep(0.01)
                    #print 'timeout 51'
                    continue
                except struct.error:
                    break  # chrome doesn't send a close-frame
                fin, mask = bool(data[0] & 0x80), bool(data[1] & 0x80)
                opcode = self._OPCODES[data[0] & 0xF]
                if opcode == 'close':
                    break
                elif opcode == 'pong':
                    self.on_pong()
                    continue
                length = data[1] & 0x7F
                if length == 126:
                    length = struct.unpack('!H', self.request.recv(2))[0]
                elif length == 127:
                    length = struct.unpack('!Q', self.request.recv(8))[0]
                mask = bytearray(self.request.recv(4)) if mask else None
                data = bytearray(self.request.recv(length))
                if mask is not None:
                    data = bytearray((b ^ mask[i % 4]) for (i, b) in enumerate(data))
                if opcode == 'continue':
                    assert buf is not None
                    opcode = buf_op
                elif opcode == 'ping':
                    self._send(10, data)
                    continue
                elif buf is not None:
                    logging.warning('Received a new frame while waiting for another to finish, '
                                    'discarding {} bytes of {}'.format(len(buf), buf_op))
                    buf = buf_op = None
                if opcode == 'text':
                    data = str_t(data, 'utf8')
                elif opcode != 'binary':
                    logging.warning('Unknown websocket opcode {}'.format(opcode))
                    continue
                if buf is None:
                    buf = data
                    buf_op = opcode
                else:
                    buf += data
                if fin:
                    self.on_message(buf)
                    buf = buf_op = None
        finally:
            self.on_close()

    def finish(self):
        pass

    def _send(self, opcode, data):
        length = len(data)
        out = bytearray()
        out.append(0x80 | opcode)
        if length <= 125:
            out.append(length)
        elif length <= 65535:
            out.append(126)
            out.extend(struct.pack('!H', length))
        else:
            out.append(127)
            out.extend(struct.pack('!Q', length))
        if length:
            out.extend(data)
        self.request.sendall(out)

    # Below is the partial API from tornado.websocket.WebSocketHandler
    def ping(self):
        self._send(9, '')

    def should_close(self):
        """When this returns true, the message loop will exit."""
        return False

    def write_message(self, message, binary=False):
        if binary:
            self._send(2, message)
        else:
            self._send(1, message.encode('utf8'))

    # Event handlers
    def on_pong(self):
        pass

    def open(self):
        pass

    def on_close(self):
        pass

    def on_message(self, message):
        raise NotImplementedError('Required method on_message() not implemented.')


class DharmaTCPServer(ThreadingMixIn, TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class DharmaWebSocketServer(object):
    def __init__(self, machine, address=("127.0.0.1", 9090)):
        self.server = None
        self.machine = machine
        self.address = address

    def start(self):
        machine = self.machine

        class DharmaWebSocketHandler(BaseWebSocketHandler):
            def on_message(self, msg):
                msg = json.loads(msg)
                if msg.get("status") == "open":
                    logging.info("WebSocket connection opened.")
                if msg.get("status") in ("open", "success"):
                    self.write_message(machine.generate_content())
                elif msg.get("status") == "closed":
                    logging.info("WebSocket connection closed.")
                else:
                    logging.error("WebSocket received unexpected message %r", msg)

        try:
            self.server = DharmaTCPServer(self.address, DharmaWebSocketHandler)
        except Exception as e:
            logging.error("Unable to start WebSocket server: %s", e)
            return
        logging.info("Socket server is listening at %s:%d", *self.address)
        self.server.serve_forever()

    def stop(self):
        if self.server is None:
            return
        try:
            logging.info("Stopping WebSocket server.")
            self.server.shutdown()
        except Exception as e:
            logging.error("Unable to shutdown WebSocket server: %s", e)
