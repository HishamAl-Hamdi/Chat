import threading
import socket
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

# Global variables to manage clients and their names
clients = []  # List to hold connected client sockets
client_names = {}  # Dictionary to map client sockets to their names
public_keys = {}  # Dictionary to store clients' public keys

# Function to generate RSA keys
def generate_rsa_keys():
    # Generate a private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    # Derive the corresponding public key
    public_key = private_key.public_key()
    return private_key, public_key

# Caesar cipher encryption function
def caesar_encrypt(message, shift):
    encrypted = []  # List to hold encrypted characters
    for char in message:
        if char.isalpha():  # Check if the character is a letter
            shifted = ord(char) + shift  # Shift the character
            # Wrap around if the shift goes past 'z' or 'Z'
            if char.islower():
                if shifted > ord('z'):
                    shifted -= 26
            elif char.isupper():
                if shifted > ord('Z'):
                    shifted -= 26
            encrypted.append(chr(shifted))  # Convert back to character
        else:
            encrypted.append(char)  # Non-alpha characters remain unchanged
    return ''.join(encrypted)  # Join and return the encrypted message

# Caesar cipher decryption function
def caesar_decrypt(encrypted_message, shift):
    decrypted = []  # List to hold decrypted characters
    for char in encrypted_message:
        if char.isalpha():  # Check if the character is a letter
            shifted = ord(char) - shift  # Shift the character back
            # Wrap around if the shift goes before 'a' or 'A'
            if char.islower():
                if shifted < ord('a'):
                    shifted += 26
            elif char.isupper():
                if shifted < ord('A'):
                    shifted += 26
            decrypted.append(chr(shifted))  # Convert back to character
        else:
            decrypted.append(char)  # Non-alpha characters remain unchanged
    return ''.join(decrypted)  # Join and return the decrypted message

# Function to handle each client connection
def handle_client(client_socket):
    # Generate RSA keys for this client
    private_key, public_key = generate_rsa_keys()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Send the public key to the client
    client_socket.send(public_key_bytes)

    # Receive the client's public key
    client_public_key_bytes = client_socket.recv(1024)
    client_public_key = serialization.load_pem_public_key(
        client_public_key_bytes,
        backend=default_backend()
    )

    # Generate a shared symmetric key for AES
    shared_key = os.urandom(32)  # Generate a random 256-bit key
    encrypted_shared_key = client_public_key.encrypt(
        shared_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),  # Mask generation function
            algorithm=hashes.SHA256(),  # Hashing algorithm
            label=None
        )
    )
    # Send the encrypted shared key to the client
    client_socket.send(encrypted_shared_key)

    # Store client information
    name = client_socket.recv(1024).decode()  # Receive the client's name
    client_names[client_socket] = name  # Map the socket to the name
    clients.append(client_socket)  # Add the socket to the clients list
    public_keys[client_socket] = public_key  # Store the client's public key

    print(f"{name} has joined the chat!")  # Inform the server console
    broadcast(f"{name} has joined the chat!", exclude=client_socket)  # Notify other clients

    while True:
        try:
            # Receive an encrypted message from the client
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break  # Break if the client disconnects
            
            # Decrypt the received message using the shared key
            cipher = Cipher(algorithms.AES(shared_key), modes.CBC(encrypted_message[:16]))
            decryptor = cipher.decryptor()
            message = decryptor.update(encrypted_message[16:]) + decryptor.finalize()
            message = message.decode().strip()  # Decode and clean the message

            if message.lower() == 'end':
                broadcast(f"{name} has left the chat!", exclude=client_socket)  # Notify others
                clients.remove(client_socket)  # Remove client from the list
                del client_names[client_socket]  # Remove from names dictionary
                client_socket.close()  # Close the client socket
                print(f"{name} has left the chat.")  # Inform the server console
                break
            else:
                broadcast(f"{name}: {message}", exclude=client_socket)  # Broadcast the message
                print(f"{name}: {message}")  # Server displays the message
        except Exception as e:
            print(f"Error: {e}")  # Print any errors
            break

# Function to broadcast messages to all clients
def broadcast(message, exclude=None):
    # Encrypt the message using Caesar cipher before broadcasting
    encrypted_message = caesar_encrypt(message, shift=3)
    for client in clients:
        if client != exclude:  # Exclude the sender
            try:
                client.send(encrypted_message.encode())  # Send encrypted message
            except:
                client.close()  # Close the client if there's an error
                clients.remove(client)  # Remove from clients list

# Function to start the server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    server.bind(("127.0.0.1", 8888))  # Bind to localhost on port 8888
    server.listen()  # Start listening for connections
    print("Server is listening for connections...")
    
    while True:
        client_socket, addr = server.accept()  # Accept a new client connection
        print(f"Connection from {addr} accepted.")  # Print client address
        threading.Thread(target=handle_client, args=(client_socket,)).start()  # Handle client in a new thread

# Function for clients to send messages
def sending_messages(client_socket, name, shared_key): 
    while True:
        message = input(">> ")  # Get user input
        if message.lower() == 'end':  # Check for exit command
            client_socket.send(message.encode())  # Send exit message
            client_socket.close()  # Close the socket
            break
        
        # Encrypt message
        iv = os.urandom(16)  # Generate a random IV for AES
        cipher = Cipher(algorithms.AES(shared_key), modes.CBC(iv))  # Create a cipher object
        encryptor = cipher.encryptor()  # Create an encryptor

        # Pad the message to be a multiple of the block size
        padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()  # Create a padder
        padded_message = padder.update(message.encode()) + padder.finalize()  # Pad the message
        
        encrypted_message = iv + encryptor.update(padded_message) + encryptor.finalize()  # Encrypt the message
        
        client_socket.send(encrypted_message)  # Send the encrypted message

# Function for clients to receive messages
def receiving_messages(client_socket):
    while True:
        try:
            encrypted_message = client_socket.recv(1024).decode()  # Receive encrypted message
            # Decrypt the received encrypted message
            decrypted_message = caesar_decrypt(encrypted_message, shift=3)
            print(decrypted_message)  # Print the decrypted message
        except:
            print("Disconnected from server.")  # Inform if disconnected
            break

# Function to start the client
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    client_socket.connect(("127.0.0.1", 8888))  # Connect to the server

    # Receive the server's public key
    server_public_key_bytes = client_socket.recv(1024)
    server_public_key = serialization.load_pem_public_key(
        server_public_key_bytes,
        backend=default_backend()
    )

    # Generate client's RSA keys
    private_key, public_key = generate_rsa_keys()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    client_socket.send(public_key_bytes)  # Send client's public key to server

    # Receive the encrypted shared key
    encrypted_shared_key = client_socket.recv(1024)
    shared_key = private_key.decrypt(
        encrypted_shared_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    name = input("Enter your name: ")  # Get client's name
    client_socket.send(name.encode())  # Send name to server

    # Start threads for sending and receiving messages
    threading.Thread(target=sending_messages, args=(client_socket, name, shared_key)).start()
    threading.Thread(target=receiving_messages, args=(client_socket,)).start()

# Main function to choose server or client mode
def main():
    choice = input("Do you want to host (1) or connect (2): ")  # User choice

    if choice == "1":
        start_server()  # Start the server
    elif choice == "2":
        start_client()  # Start the client
    else:
        print("Invalid choice. Exiting...")  # Handle invalid input

if __name__ == "__main__":
    main()  # Execute the main function