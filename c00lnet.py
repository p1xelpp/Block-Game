import json
import socket
import threading

class Server:
    def __init__(self, host='0.0.0.0', port=27015):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
        self.running = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()

        listener = threading.Thread(target=self._accept_loop, daemon=True)
        listener.start()
        print(f"Server listening on {self.host}:{self.port}")

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.sock.accept()
            except OSError:
                break

            print(f"Client connected: {addr}")
            client.settimeout(None)
            with self.lock:
                self.clients.append(client)
            handler = threading.Thread(target=self._client_loop, args=(client,), daemon=True)
            handler.start()

    def _client_loop(self, client):
        buffer = b''
        try:
            while self.running:
                try:
                    data = client.recv(4096)
                except (ConnectionResetError, ConnectionAbortedError, OSError):
                    break
                if not data:
                    break
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode('utf-8'))
                    except Exception:
                        continue
                    self.broadcast(msg, exclude=client)
        finally:
            with self.lock:
                if client in self.clients:
                    self.clients.remove(client)
            try:
                client.close()
            except Exception:
                pass
            print("Client disconnected")

    def broadcast(self, msg, exclude=None):
        data = (json.dumps(msg) + "\n").encode('utf-8')
        with self.lock:
            for client in list(self.clients):
                if client is exclude:
                    continue
                try:
                    client.sendall(data)
                except Exception:
                    self.clients.remove(client)
                    client.close()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass
        with self.lock:
            for client in list(self.clients):
                try:
                    client.close()
                except Exception:
                    pass
            self.clients.clear()


class ServerClient:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.on_message = None
        self._receiver = None
        self.running = False

    def connect(self, ip, port=27015):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.connected = True
            self.running = True
            self._receiver = threading.Thread(target=self._recv_loop, daemon=True)
            self._receiver.start()
            print(f"Connected to server {ip}:{port}")
            return True
        except Exception as e:
            print(f"Connect failed: {e}")
            return False

    def _recv_loop(self):
        buffer = b''
        try:
            while self.running:
                try:
                    data = self.sock.recv(4096)
                except (ConnectionResetError, ConnectionAbortedError, OSError):
                    break
                if not data:
                    break
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode('utf-8'))
                    except Exception:
                        continue
                    print(f"[NETWORK CLIENT] received raw message: {msg}")
                    if self.on_message:
                        self.on_message(msg)
                    else:
                        print("[NETWORK CLIENT] warning: on_message callback not set")
        finally:
            self.connected = False
            self.running = False
            try:
                self.sock.close()
            except Exception:
                pass
            print("Disconnected from server")

    def send(self, msg):
        if not self.connected:
            print(f"[NETWORK CLIENT] send skipped, not connected: {msg}")
            return
        try:
            data = (json.dumps(msg) + "\n").encode('utf-8')
            self.sock.sendall(data)
            print(f"[NETWORK CLIENT] sent: {msg}")
        except Exception as e:
            print(f"[NETWORK CLIENT] send failed: {e} msg={msg}")
            self.connected = False

    def close(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.connected = False
