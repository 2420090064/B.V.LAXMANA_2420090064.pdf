import socket
import threading

HOST = "127.0.0.1"
PORT = 5000


# ==================================================
# CREATE PLAYFAIR KEY MATRIX
# ==================================================

def build_matrix(keyword):

    keyword = keyword.upper()
    keyword = keyword.replace("J", "I")

    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"

    characters = []

    for ch in keyword + alphabet:
        if ch.isalpha() and ch not in characters:
            characters.append(ch)

    matrix = []

    for i in range(0, 25, 5):
        matrix.append(characters[i:i + 5])

    return matrix


# ==================================================
# DISPLAY MATRIX
# ==================================================

def display_matrix(matrix):

    print("\n+---+---+---+---+---+")

    for row in matrix:
        print("| " + " | ".join(row) + " |")
        print("+---+---+---+---+---+")


# ==================================================
# FIND CHARACTER POSITION
# ==================================================

def position(matrix, letter):

    if letter == "J":
        letter = "I"

    for r in range(5):
        for c in range(5):

            if matrix[r][c] == letter:
                return r, c

    return None


# ==================================================
# PREPARE PLAINTEXT
# ==================================================

def format_plaintext(message):

    message = message.upper()
    message = message.replace("J", "I")

    message = "".join(
        ch for ch in message
        if ch.isalpha()
    )

    pairs = []
    index = 0

    while index < len(message):

        first = message[index]

        if index + 1 >= len(message):
            pairs.append(first + "X")
            index += 1

        else:

            second = message[index + 1]

            if first == second:
                pairs.append(first + "X")
                index += 1

            else:
                pairs.append(first + second)
                index += 2

    return pairs


# ==================================================
# PLAYFAIR ENCRYPTION
# ==================================================

def playfair_encrypt(message, matrix):

    pairs = format_plaintext(message)
    result = ""

    for pair in pairs:

        first = pair[0]
        second = pair[1]

        r1, c1 = position(matrix, first)
        r2, c2 = position(matrix, second)

        # Same row
        if r1 == r2:

            result += matrix[r1][(c1 + 1) % 5]
            result += matrix[r2][(c2 + 1) % 5]

        # Same column
        elif c1 == c2:

            result += matrix[(r1 + 1) % 5][c1]
            result += matrix[(r2 + 1) % 5][c2]

        # Rectangle rule
        else:

            result += matrix[r1][c2]
            result += matrix[r2][c1]

    return result


# ==================================================
# PLAYFAIR DECRYPTION
# ==================================================

def playfair_decrypt(ciphertext, matrix):

    plaintext = ""

    for i in range(0, len(ciphertext), 2):

        first = ciphertext[i]
        second = ciphertext[i + 1]

        r1, c1 = position(matrix, first)
        r2, c2 = position(matrix, second)

        # Same row
        if r1 == r2:

            plaintext += matrix[r1][(c1 - 1) % 5]
            plaintext += matrix[r2][(c2 - 1) % 5]

        # Same column
        elif c1 == c2:

            plaintext += matrix[(r1 - 1) % 5][c1]
            plaintext += matrix[(r2 - 1) % 5][c2]

        # Rectangle rule
        else:

            plaintext += matrix[r1][c2]
            plaintext += matrix[r2][c1]

    return plaintext


# ==================================================
# RECEIVE CLIENT MESSAGE
# ==================================================

def client_receiver(connection, matrix):

    while True:

        try:

            data = connection.recv(4096)

            if not data:
                print("\nClient disconnected.")
                break

            encrypted_message = data.decode()

            if encrypted_message.lower() == "exit":

                print("\nClient stopped the communication.")
                break

            decrypted_message = playfair_decrypt(
                encrypted_message,
                matrix
            )

            print("\n----------------------------------------")
            print("       MESSAGE FROM CLIENT")
            print("----------------------------------------")
            print("Ciphertext :", encrypted_message)
            print("Plaintext  :", decrypted_message)
            print("----------------------------------------")

        except ConnectionResetError:

            print("\nClient connection lost.")
            break

        except Exception as error:

            print("\nReceiving error:", error)
            break


# ==================================================
# SEND MESSAGE TO CLIENT
# ==================================================

def send_messages(connection, matrix):

    while True:

        try:

            message = input("\nServer: ")

            if message.lower() == "exit":

                connection.sendall(
                    "exit".encode()
                )

                break

            if message.strip() == "":
                print("Message cannot be empty.")
                continue

            encrypted_message = playfair_encrypt(
                message,
                matrix
            )

            print("Encrypted :", encrypted_message)

            connection.sendall(
                encrypted_message.encode()
            )

        except BrokenPipeError:

            print("\nClient disconnected.")
            break

        except ConnectionResetError:

            print("\nConnection lost.")
            break


# ==================================================
# START SERVER
# ==================================================

def run_server():

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (HOST, PORT)
    )

    server_socket.listen(1)

    print("\n======================================")
    print("        PLAYFAIR CIPHER SERVER")
    print("======================================")
    print("IP Address :", HOST)
    print("Port       :", PORT)
    print("\nWaiting for client...")

    connection, address = server_socket.accept()

    print("\nClient connected!")
    print("Client address:", address)

    # ------------------------------------------
    # KEY
    # ------------------------------------------

    keyword = input("\nEnter Playfair keyword: ")

    matrix = build_matrix(keyword)

    print("\nGenerated Playfair Matrix:")

    display_matrix(matrix)

    print("\n======================================")
    print("          SERVER READY")
    print("======================================")
    print("Two-way communication enabled.")
    print("Type 'exit' to close the server.")
    print("======================================")

    # ------------------------------------------
    # RECEIVING THREAD
    # ------------------------------------------

    receiver_thread = threading.Thread(
        target=client_receiver,
        args=(connection, matrix),
        daemon=True
    )

    receiver_thread.start()

    # ------------------------------------------
    # SEND LOOP
    # ------------------------------------------

    send_messages(
        connection,
        matrix
    )

    # ------------------------------------------
    # CLOSE
    # ------------------------------------------

    connection.close()
    server_socket.close()

    print("\nServer closed successfully.")


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    run_server()