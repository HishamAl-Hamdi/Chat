Names of Group members:
1-Hisham Al-Hamdi
2-Wadhah Ameen
3-Khaled Al-Haj

[Youtube Link here](https://youtu.be/0fMv2lmzJtY?si=KOR4DlaPOl9_d756))

Chat Application with Encryption
This is a Python-based chat application that allows multiple clients to communicate securely over a network. The application uses RSA for key exchange and AES for message encryption, along with a Caesar cipher for additional message obfuscation.

Features
Secure Communication: Utilizes RSA for secure key exchange and AES for encrypting messages.
Multi-client Support: Handles multiple clients simultaneously using threading.
User-friendly Interface: Simple command-line interface for user interaction.
Encryption: Messages are encrypted before being sent and decrypted upon receipt, ensuring privacy.
Technologies Used
Python
Sockets for networking
Cryptography library for encryption
Getting Started
Prerequisites
Python 3.x
Cryptography library
You can install the required library using pip:

bash

Copy
pip install cryptography
Running the Application
Start the Server:
Run the server code to listen for incoming client connections.
bash

Copy
python chat_app.py
The server will start listening for connections on 127.0.0.1:8888.
Connect a Client:
Open another terminal and run the client code.
bash

Copy
python chat_app.py
You will be prompted to choose whether to host a server or connect as a client. Enter 2 to connect.
Chatting:
Once connected, enter your name and start chatting.
Type your messages and press Enter to send.
Type end to exit the chat.
Code Structure
Server: Handles client connections, message broadcasting, and encryption/decryption.
Client: Connects to the server, sends and receives messages, and manages user input.
Example Usage
Start the server:

Copy
Server is listening for connections...
Connect a client:

Copy
Enter your name: Alice
Alice has joined the chat!
Send a message:

Copy
>> Hello, everyone!
Receive a message:

Copy
Bob: Hi, Alice!
Security Considerations
The application employs encryption to secure messages from eavesdropping.
Ensure to use secure environments when deploying this application in production.
Contributing
Feel free to contribute to this project by submitting issues or pull requests.

License
This project is open-source and available under the MIT License.
