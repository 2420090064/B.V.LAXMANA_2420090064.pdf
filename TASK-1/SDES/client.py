import socket
import threading

HOST = "127.0.0.1"
PORT = 5000


# =====================================================
# PLAYFAIR CIPHER CLASS
# =====================================================

class PlayfairCipher:

    def __init__(self, keyword):
        self.table = self.generate_table(keyword)

    # -------------------------------------------------
    # Generate 5 x 5 matrix
    # -------------------------------------------------

    def generate_table(self, keyword):

        keyword = keyword.upper().replace("J", "I")

        sequence = []

        for letter in keyword:
            if letter.isalpha() and letter not in sequence:
                sequence.append(letter)

        for letter in "ABCDEFGHIKLMNOPQRSTUVWXYZ":
            if letter not in sequence:
                sequence.append(letter)

        return [
            sequence[0:5],
            sequence[5:10],
            sequence[10:15],
            sequence[15:20],
            sequence[20:25]
        ]

    # -------------------------------------------------
    # Display matrix
    # -------------------------------------------------

    def show_table(self):

        print("\n+---+---+---+---+---+")

        for row in self.table:
            print(
                "| " +
                " | ".join(row) +
                " |"
            )
            print("+---+---+---+---+---+")

    # -------------------------------------------------
    # Find row and column
    # -------------------------------------------------

    def locate(self, letter):

        if letter == "J":
            letter = "I"

        for row in range(5):
            for column in range(5):

                if self.table[row][column] == letter:
                    return row, column

        return -1, -1

    # -------------------------------------------------
    # Prepare plaintext
    # -------------------------------------------------

    def prepare(self, message):

        message = message.upper()
        message = message.replace("J", "I")

        cleaned = ""

        for letter in message:
            if letter.isalpha():
                cleaned += letter

        result = []
        index = 0

        while index < len(cleaned):

            first = cleaned[index]

            if index + 1 == len(cleaned):
                result.append(first + "X")
                index += 1

            else:

                second = cleaned[index + 1]

                if first == second:
                    result.append(first + "X")
                    index += 1

                else:
                    result.append(first + second)
                    index += 2

        return result

    # -------------------------------------------------
    # Encrypt one pair
    # -------------------------------------------------

    def encrypt_pair(self, first, second):

        r1, c1 = self.locate(first)
        r2, c2 = self.locate(second)

        # Same row
        if r1 == r2:

            first = self.table[r1][(c1 + 1) % 5]
            second = self.table[r2][(c2 + 1) % 5]

        # Same column
        elif c1 == c2:

            first = self.table[(r1 + 1) % 5][c1]
            second = self.table[(r2 + 1) % 5][c2]

        # Rectangle
        else:

            first = self.table[r1][c2]
            second = self.table[r2][c1]

        return first + second

    # -------------------------------------------------
    # Decrypt one pair
    # -------------------------------------------------

    def decrypt_pair(self, first, second):

        r1, c1 = self.locate(first)
        r2, c2 = self.locate(second)

        # Same row
        if r1 == r2:

            first = self.table[r1][(c1 - 1) % 5]
            second = self.table[r2][(c2 - 1) % 5]

        # Same column
        elif c1 == c2:

            first = self.table[(r1 - 1) % 5][c1]
            second = self.table[(r2 - 1) % 5][c2]

        # Rectangle
        else:

            first = self.table[r1][c2]
            second = self.table[r2][c1]

        return first + second

    # -------------------------------------------------
    # Encrypt complete message
    # -------------------------------------------------

    def encrypt(self, message):

        pairs = self.prepare(message)
        encrypted = ""

        for pair in pairs:
            encrypted += self.encrypt_pair(
                pair[0],
                pair[1]
            )

        return encrypted

    # -------------------------------------------------
    # Decrypt complete message
    # -------------------------------------------------

    def decrypt(self, message):

        decrypted = ""

        for index in range(0, len(message), 2):

            pair = self.decrypt_pair(
                message[index],
                message[index + 1]
            )

            decrypted += pair

        return decrypted


# =====================================================
# RECEIVE DATA FROM CLIENT
# =====================================================

def receive_from_client(connection, cipher):

    while True:

        try:

            received = connection.recv(4096)

            if not received:
                print("\nClient disconnected.")
                break

            message = received.decode()

            if message.lower() == "exit":

                print("\nClient terminated communication.")
                break

            original_message = cipher.decrypt(message)

            print("\n========================================")
            print("          CLIENT -> SERVER")
            print("========================================")
            print("Encrypted :", message)
            print("Decrypted :", original_message)
            print("========================================")

        except ConnectionResetError:

            print("\nClient connection was lost.")
            break

        except Exception as error:

            print("\nError:", error)
            break


# =====================================================
# SEND DATA TO CLIENT
# =====================================================

def send_to_client(connection, cipher):

    while True:

        try:

            message = input("\nServer: ")

            if message.lower() == "exit":

                connection.sendall(
                    b"exit"
                )

                break

            if not message.strip():
                print("Please enter a message.")
                continue

            encrypted = cipher.encrypt(message)

            print("Encrypted :", encrypted)

            connection.sendall(
                encrypted.encode()
            )

        except BrokenPipeError:

            print("\nClient disconnected.")
            break

        except ConnectionResetError:

            print("\nConnection lost.")
            break


# =====================================================
# MAIN SERVER
# =====================================================

def main():

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
        (HOST, PORT)
    )

    server.listen(1)

    print("\n========================================")
    print("         PLAYFAIR CIPHER SERVER")
    print("========================================")
    print("Host :", HOST)
    print("Port :", PORT)
    print("\nWaiting for client...")

    connection, client_address = server.accept()

    print("\nClient connected!")
    print("Address:", client_address)

    # -------------------------------------------------
    # Get keyword
    # -------------------------------------------------

    keyword = input("\nEnter Playfair keyword: ")

    cipher = PlayfairCipher(keyword)

    print("\nGenerated Playfair Matrix:")

    cipher.show_table()

    print("\n========================================")
    print("             SERVER READY")
    print("========================================")
    print("Two-way communication is enabled.")
    print("Type 'exit' to close the connection.")
    print("========================================")

    # -------------------------------------------------
    # Create receiving thread
    # -------------------------------------------------

    receiver = threading.Thread(
        target=receive_from_client,
        args=(connection, cipher),
        daemon=True
    )

    receiver.start()

    # -------------------------------------------------
    # Start sending
    # -------------------------------------------------

    send_to_client(
        connection,
        cipher
    )

    # -------------------------------------------------
    # Close sockets
    # -------------------------------------------------

    connection.close()
    server.close()

    print("\nServer closed successfully.")


# =====================================================
# PROGRAM START
# =====================================================

if __name__ == "__main__":
    main()