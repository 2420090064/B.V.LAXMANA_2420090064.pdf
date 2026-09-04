import socket
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


# ==========================================
# CAESAR CIPHER
# ==========================================

def encrypt_message(message, shift):
    output = ""

    for character in message:

        if character.isupper():
            output += chr(
                (ord(character) - 65 + shift) % 26 + 65
            )

        elif character.islower():
            output += chr(
                (ord(character) - 97 + shift) % 26 + 97
            )

        else:
            output += character

    return output


def decrypt_message(message, shift):
    return encrypt_message(message, -shift)


# ==========================================
# RECEIVE MESSAGES
# ==========================================

def receive_messages(connection, shift):

    while True:

        try:
            data = connection.recv(2048)

            if not data:
                print("\nClient disconnected.")
                break

            encrypted = data.decode()

            if encrypted.strip().lower() == "exit":
                print("\nClient closed the communication.")
                break

            decrypted = decrypt_message(encrypted, shift)

            print("\n================================")
            print("        CLIENT MESSAGE")
            print("================================")
            print("Encrypted Message :", encrypted)
            print("Decrypted Message :", decrypted)
            print("================================")

        except ConnectionResetError:
            print("\nConnection lost.")
            break

        except OSError:
            break


# ==========================================
# SERVER START
# ==========================================

def start_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(
        (SERVER_HOST, SERVER_PORT)
    )

    server.listen(1)

    print("\n===================================")
    print("       CAESAR CIPHER SERVER")
    print("===================================")
    print("Server IP   :", SERVER_HOST)
    print("Server Port :", SERVER_PORT)
    print("\nWaiting for client...")

    connection, address = server.accept()

    print("\nClient connected!")
    print("Client Address:", address)

    # --------------------------------------
    # GET KEY
    # --------------------------------------

    while True:

        try:
            shift = int(input("\nEnter Caesar key (1-25): "))

            if 1 <= shift <= 25:
                break

            print("Key must be between 1 and 25.")

        except ValueError:
            print("Please enter a number.")

    print("\n===================================")
    print("      CONNECTION ESTABLISHED")
    print("===================================")
    print("Encryption Key:", shift)
    print("You can now send messages.")
    print("Type 'exit' to stop.")
    print("===================================\n")

    # --------------------------------------
    # RECEIVING THREAD
    # --------------------------------------

    receiver = threading.Thread(
        target=receive_messages,
        args=(connection, shift),
        daemon=True
    )

    receiver.start()

    # --------------------------------------
    # SEND MESSAGES
    # --------------------------------------

    while True:

        try:
            message = input("Server: ")

            if message.lower() == "exit":

                connection.sendall(
                    b"exit"
                )

                print("\nClosing server...")
                break

            encrypted = encrypt_message(
                message,
                shift
            )

            print("Encrypted Message:", encrypted)

            connection.sendall(
                encrypted.encode()
            )

        except (BrokenPipeError, ConnectionResetError):
            print("\nClient connection lost.")
            break

        except KeyboardInterrupt:
            print("\nServer interrupted.")
            break

    # --------------------------------------
    # CLOSE CONNECTION
    # --------------------------------------

    connection.close()
    server.close()

    print("Server stopped.")


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":
    start_server()