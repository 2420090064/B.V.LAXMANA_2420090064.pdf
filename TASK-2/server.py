import socket
import struct
import os
import io
import threading

from Crypto.Cipher import AES
from pypdf import PdfReader
from docx import Document


HOST = "0.0.0.0"
PORT = 5001

KEY = b"1234567890123456"
BLOCK_SIZE = 16


# ============================================================
# AES
# ============================================================

def pad(data):
    n = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([n]) * n


def unpad(data):
    n = data[-1]
    return data[:-n]


def encrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return cipher.encrypt(pad(data))


def decrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(data))


# ============================================================
# SOCKET FUNCTIONS
# ============================================================

def send_data(sock, data):
    sock.sendall(struct.pack("!Q", len(data)))
    sock.sendall(data)


def receive_all(sock, size):
    data = bytearray()

    while len(data) < size:
        packet = sock.recv(min(65536, size - len(data)))

        if not packet:
            raise ConnectionError("Connection closed.")

        data.extend(packet)

    return bytes(data)


def receive_data(sock):
    size = struct.unpack("!Q", receive_all(sock, 8))[0]
    return receive_all(sock, size)


def send_string(sock, text):
    send_data(sock, text.encode("utf-8"))


def receive_string(sock):
    return receive_data(sock).decode("utf-8")


# ============================================================
# DISPLAY PLAINTEXT
# ============================================================

def display_plaintext(filename, data):

    extension = os.path.splitext(filename)[1].lower()

    # ---------------- TEXT ----------------

    if extension in [
        ".txt", ".csv", ".py", ".java",
        ".c", ".cpp", ".html", ".css",
        ".js", ".json", ".xml"
    ]:

        text = data.decode(
            "utf-8",
            errors="replace"
        )

        print(text[:5000])

        if len(text) > 5000:
            print("\n...[remaining text not displayed]...")

        return

    # ---------------- PDF ----------------

    if extension == ".pdf":

        try:

            reader = PdfReader(
                io.BytesIO(data)
            )

            text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

            if text.strip():
                print(text[:5000])

                if len(text) > 5000:
                    print("\n...[remaining PDF text not displayed]...")
            else:
                print("[No readable PDF text found]")

        except Exception as e:

            print("[PDF extraction error]")
            print(e)

        return

    # ---------------- DOCX ----------------

    if extension == ".docx":

        try:

            document = Document(
                io.BytesIO(data)
            )

            text = ""

            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"

            print(text[:5000])

            if len(text) > 5000:
                print("\n...[remaining DOCX text not displayed]...")

        except Exception as e:

            print("[DOCX extraction error]")
            print(e)

        return

    # ---------------- BINARY ----------------

    print("[Binary file - displaying raw bytes]")
    print(data[:200])


# ============================================================
# DISPLAY RECEIVED FILE
# ============================================================

def display_received_file(
    filename,
    plaintext,
    ciphertext
):

    print("\n")
    print("=" * 70)
    print("SERVER - FILE RECEIVED")
    print("=" * 70)

    print("Direction       : CLIENT -> SERVER")
    print("File            :", filename)
    print("Plaintext size  :", len(plaintext), "bytes")
    print("Ciphertext size :", len(ciphertext), "bytes")

    print("\n----- PLAINTEXT -----")

    display_plaintext(
        filename,
        plaintext
    )

    print("\n----- CIPHERTEXT -----")

    print(
        ciphertext[:500].hex()
    )

    if len(ciphertext) > 500:
        print(
            "...[remaining ciphertext not displayed]..."
        )

    print("=" * 70)

    print("\nAES decryption completed.")
    print("Received file was NOT saved.")


# ============================================================
# RECEIVE FILE
# ============================================================

def receive_file(conn):

    try:

        command = receive_string(conn)

        if command == "FILE":

            filename = receive_string(conn)

            ciphertext = receive_data(conn)

            print(
                "\n\nEncrypted file received automatically."
            )

            plaintext = decrypt_data(
                ciphertext
            )

            display_received_file(
                filename,
                plaintext,
                ciphertext
            )

            return True

        elif command == "EXIT":

            print(
                "\nClient disconnected."
            )

            return False

        else:

            print(
                "\nUnknown command received."
            )

            return True

    except Exception as e:

        print(
            "\nReceive error:",
            e
        )

        return False


# ============================================================
# AUTOMATIC RECEIVER
# ============================================================

def automatic_receiver(conn):

    while True:

        try:

            command = receive_string(conn)

            if command == "FILE":

                filename = receive_string(conn)

                ciphertext = receive_data(conn)

                print(
                    "\n\n"
                    + "=" * 70
                )

                print(
                    "INCOMING FILE RECEIVED AUTOMATICALLY"
                )

                print(
                    "=" * 70
                )

                plaintext = decrypt_data(
                    ciphertext
                )

                display_received_file(
                    filename,
                    plaintext,
                    ciphertext
                )

            elif command == "EXIT":

                print(
                    "\nClient disconnected."
                )

                break

        except Exception:
            break


# ============================================================
# SEND FILE
# ============================================================

def send_file(conn):

    path = input(
        "\nEnter file path to send: "
    ).strip().strip('"')

    if not os.path.isfile(path):

        print(
            "\nERROR: File not found."
        )

        return

    try:

        with open(
            path,
            "rb"
        ) as file:

            plaintext = file.read()

        print(
            "\nEncrypting file using AES..."
        )

        ciphertext = encrypt_data(
            plaintext
        )

        send_string(
            conn,
            "FILE"
        )

        send_string(
            conn,
            os.path.basename(path)
        )

        send_data(
            conn,
            ciphertext
        )

        print(
            "\nAES encryption completed."
        )

        print(
            "File encrypted and sent to client."
        )

        print(
            "Client will automatically receive it."
        )

    except Exception as e:

        print(
            "\nSend error:",
            e
        )


# ============================================================
# SERVER START
# ============================================================

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

print("=" * 70)
print("             AES FILE TRANSFER SERVER")
print("=" * 70)

print("\nAES Algorithm : AES")
print("AES Mode      : ECB")
print("AES Key       :", KEY.decode())

print("\nWaiting for client...")

conn, address = server.accept()

print(
    "\nConnected to:",
    address
)

print(
    "\nServer ready."
)


# ============================================================
# AUTOMATIC RECEIVE THREAD
# ============================================================

receiver = threading.Thread(
    target=automatic_receiver,
    args=(conn,),
    daemon=True
)

receiver.start()


# ============================================================
# SERVER MENU
# ============================================================

while True:

    print("\n")
    print("=" * 70)
    print("SERVER MENU")
    print("=" * 70)

    print("1. Encrypt and Send File to Client")
    print("2. Wait / Receive File from Client")
    print("3. Exit")

    print("=" * 70)

    try:

        choice = input(
            "Enter server choice: "
        ).strip()

    except KeyboardInterrupt:

        break

    if choice == "1":

        send_file(conn)

    elif choice == "2":

        print(
            "\nServer is already automatically listening."
        )

        print(
            "Waiting for a file from Client..."
        )

    elif choice == "3":

        try:
            send_string(
                conn,
                "EXIT"
            )
        except:
            pass

        print(
            "\nServer stopped."
        )

        break

    else:

        print(
            "\nInvalid choice. Enter 1, 2 or 3."
        )


try:
    conn.close()
    server.close()
except:
    pass