# Secure Command and Control Communication Simulator

## Project Overview

This project implements a secure, encrypted client-server communication system inspired by Command-and-Control (C2) architectures used in distributed systems and cybersecurity research.

The system consists of:
- A **Controller (Server)** that sends commands
- One or more **Agents (Clients)** that execute commands
- A secure communication layer using **AES-GCM encryption**
- A reliable message transport system over TCP sockets

The goal is to study:
- Secure remote command execution
- Encrypted network communication
- Basic C2-style architecture design
- Client-server distributed systems


## Features

- TCP-based framed communication protocol
- AES-GCM encryption for all messages
- Multi-client support (threaded server)
- Remote command execution on agent machines
- Structured JSON messaging format
- Command response handling system


## Architecture
- Controller (Server)
- ↓ encrypted commands
- Agents (Clients)
- ↓ encrypted responses
- Controller logs outputs

## Message Flow
1. Server sends command (`msg`)
2. Agent decrypts and executes command
3. Agent sends response (`resp`)
4. Server decrypts and displays output


## Security Layer

- AES-GCM symmetric encryption
- Random nonce per message
- SHA-256 derived session key
- JSON-based structured payloads


## How to Run

### 1. Install dependencies
    pip install cryptography
### 2. Start Server
    python server.py
### 3. Start Agent
    python agent.py
### 4. Send command or ping agent from server


