import socket
import threading

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


# --------------------------------
# CAESAR CIPHER FUNCTIONS
# --------------------------------

def caesar_encrypt(message, shift):
    encrypted = ""

    for char in message:
        if 'A' <= char <= 'Z':
            encrypted += chr((ord(char) - 65 + shift) % 26 + 65)

        elif 'a' <= char <= 'z':
            encrypted += chr((ord(char) - 97 + shift) % 26 + 97)

        else:
            encrypted += char

    return encrypted


def caesar_decrypt(message, shift):
    return caesar_encrypt(message, -shift)


# --------------------------------
# RECEIVE DATA FROM SERVER
# --------------------------------

def receive_data(sock, shift):

    while True:
        try:
            data = sock.recv(2048)

            if not data:
                print("\nConnection closed by server.")
                break

            encrypted_message = data.decode()

            if encrypted_message == "exit":
                print("\nServer terminated the connection.")
                break

            decrypted_message = caesar_decrypt(
                encrypted_message,
                shift
            )

            print("\n--------------------------------")
            print("Message received from server")
            print("Encrypted :", encrypted_message)
            print("Decrypted :", decrypted_message)
            print("--------------------------------")
            print("Client: ", end="", flush=True)

        except ConnectionResetError:
            print("\nServer connection lost.")
            break

        except:
            break


# --------------------------------
# CLIENT PROGRAM
# --------------------------------

def start_client():

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        client.connect(
            (SERVER_IP, SERVER_PORT)
        )

    except ConnectionRefusedError:
        print("Unable to connect to server.")
        return

    print("\n==============================")
    print("     CAESAR CIPHER CLIENT")
    print("==============================")

    while True:
        try:
            shift = int(input("Enter Caesar key (1-25): "))

            if 1 <= shift <= 25:
                break

            print("Please enter a key between 1 and 25.")

        except ValueError:
            print("Enter a valid number.")

    print("\nConnected successfully!")
    print("Two-way communication started.")
    print("Type 'exit' to close the connection.\n")

    # Start receiving thread
    receiver = threading.Thread(
        target=receive_data,
        args=(client, shift),
        daemon=True
    )

    receiver.start()

    # Sending messages
    while True:

        message = input("Client: ")

        if message.lower() == "exit":
            client.sendall(b"exit")
            print("Closing connection...")
            break

        encrypted_message = caesar_encrypt(
            message,
            shift
        )

        print("Encrypted :", encrypted_message)

        client.sendall(
            encrypted_message.encode()
        )

    client.close()

    print("Client stopped.")


# --------------------------------
# MAIN
# --------------------------------

if __name__ == "__main__":
    start_client()