#importing libraries
import socket
import threading

from crypto_utils import decrypt_payload, derive_key, encrypt_payload
from transport import recv_frame, send_frame

HOST = "127.0.0.1"
PORT = 9999
SHARED_SECRET = b"RedTeamSecretKey12345!"
AES_KEY = derive_key(SHARED_SECRET)
# hi 

class C2Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        self.clients = []
        self.clients_lock = threading.Lock()
        self.running = True
        print(f"[+] Controller Listening on {HOST}:{PORT}")

    def accept_loop(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
            except OSError:
                break

            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()

    def handle_client(self, client_socket, addr):
        client = None
        try:
            packet = recv_frame(client_socket)
            if not packet:
                return

            hello = decrypt_payload(AES_KEY, packet)
            agent_id = hello.get("payload", {}).get("id", "unknown")

            client = {"sock": client_socket, "addr": addr, "id": agent_id, "lock": threading.Lock()}
            with self.clients_lock:
                self.clients.append(client)

            print(f"[+] Client connected from {addr} (id={agent_id})")

            while True:
                packet = recv_frame(client_socket)
                if not packet:
                    break

                message = decrypt_payload(AES_KEY, packet)
                self.print_message(client, message)

        except Exception as e:
            print(f"[!] Connection error from {addr}: {e}")
        finally:
            if client:
                with self.clients_lock:
                    if client in self.clients:
                        self.clients.remove(client)

            try:
                client_socket.close()
            except Exception:
                pass

    def print_message(self, client, message):
        msg_type = message.get("type", "unknown")
        payload = message.get("payload", "")
        output = message.get("output", "")
        status = message.get("status","")

        print(f"[{client['id']}] {msg_type}: {payload}\noutput{output}\nstatus : {status}")

    def send_to_client(self, client, message):
        packet = encrypt_payload(AES_KEY, message)
        with client["lock"]:
            send_frame(client["sock"], packet)

    def broadcast(self, msg_type, payload):
        with self.clients_lock:
            clients = list(self.clients)

        for client in clients:
            try:
                self.send_to_client(client, {"type": msg_type, "payload": payload})
            except Exception as e:
                print(f"[!] Send error to {client['id']}: {e}")

    def run_console(self):
        print("[+] Type messages to broadcast. Use 'ping' or 'quit'.")
        while True:
            try:
                text = input("msg> ").strip()
            except EOFError:
                text = "quit"

            if not text:
                continue
            if text.lower() == "quit":
                break
            if text.lower() == "ping":
                self.broadcast("ping", "ping")
                continue

            self.broadcast("msg", text)

        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    server = C2Server()
    accept_thread = threading.Thread(target=server.accept_loop)
    accept_thread.daemon = True
    accept_thread.start()

    try:
        server.run_console()
    except KeyboardInterrupt:
        server.running = False
        try:
            server.server_socket.close()
        except Exception:
            pass
        print("\n[+] Controller Shutting Down...")
