import socket
import struct
import os
import io
import threading

from Crypto.Cipher import AES
from pypdf import PdfReader
from docx import Document


HOST = "127.0.0.1"
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

        packet = sock.recv(
            min(65536, size - len(data))
        )

        if not packet:
            raise ConnectionError(
                "Connection closed."
            )

        data.extend(packet)

    return bytes(data)


def receive_data(sock):

    size = struct.unpack(
        "!Q",
        receive_all(sock, 8)
    )[0]

    return receive_all(
        sock,
        size
    )


def send_string(sock, text):

    send_data(
        sock,
        text.encode("utf-8")
    )


def receive_string(sock):

    return receive_data(
        sock
    ).decode("utf-8")


# ============================================================
# DISPLAY PLAINTEXT
# ============================================================

def display_plaintext(filename, data):

    extension = os.path.splitext(
        filename
    )[1].lower()

    # TEXT

    if extension in [
        ".txt", ".csv", ".py", ".java",
        ".c", ".cpp", ".html", ".css",
        ".js", ".json", ".xml"
    ]:

        text = data.decode(
            "utf-8",
            errors="replace"
        )

        print(
            text[:5000]
        )

        if len(text) > 5000:
            print(
                "\n...[remaining text not displayed]..."
            )

        return

    # PDF

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

                print(
                    text[:5000]
                )

            else:

                print(
                    "[No readable PDF text found]"
                )

        except Exception as e:

            print(
                "[PDF extraction error]"
            )

            print(e)

        return

    # DOCX

    if extension == ".docx":

        try:

            document = Document(
                io.BytesIO(data)
            )

            text = ""

            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"

            print(
                text[:5000]
            )

        except Exception as e:

            print(
                "[DOCX extraction error]"
            )

            print(e)

        return

    # BINARY

    print(
        "[Binary file - displaying raw bytes]"
    )

    print(
        data[:200]
    )


# ============================================================
# CLIENT RECEIVED FILE
# ============================================================

def display_received_file(
    filename,
    plaintext,
    ciphertext
):

    print("\n")
    print("=" * 70)
    print("CLIENT - FILE RECEIVED")
    print("=" * 70)

    print(
        "Direction       : SERVER -> CLIENT"
    )

    print(
        "File            :",
        filename
    )

    print(
        "Plaintext size  :",
        len(plaintext),
        "bytes"
    )

    print(
        "Ciphertext size :",
        len(ciphertext),
        "bytes"
    )

    print(
        "\n----- PLAINTEXT -----"
    )

    display_plaintext(
        filename,
        plaintext
    )

    print(
        "\n----- CIPHERTEXT -----"
    )

    print(
        ciphertext[:500].hex()
    )

    if len(ciphertext) > 500:

        print(
            "...[remaining ciphertext not displayed]..."
        )

    print("=" * 70)

    print(
        "\nAES decryption completed."
    )

    print(
        "Received file was NOT saved."
    )


# ============================================================
# AUTOMATIC RECEIVE
# ============================================================

def automatic_receiver(client):

    while True:

        try:

            command = receive_string(
                client
            )

            if command == "FILE":

                filename = receive_string(
                    client
                )

                ciphertext = receive_data(
                    client
                )

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
                    "\nServer disconnected."
                )

                break

        except Exception:
            break


# ============================================================
# SEND FILE
# ============================================================

def send_file(client):

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
            client,
            "FILE"
        )

        send_string(
            client,
            os.path.basename(path)
        )

        send_data(
            client,
            ciphertext
        )

        print(
            "\nAES encryption completed."
        )

        print(
            "File encrypted and sent to server."
        )

        print(
            "Server will automatically receive it."
        )

    except Exception as e:

        print(
            "\nSend error:",
            e
        )


# ============================================================
# CLIENT START
# ============================================================

client = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

client.connect(
    (HOST, PORT)
)

print("=" * 70)
print("             AES FILE TRANSFER CLIENT")
print("=" * 70)

print(
    "\nConnected to server."
)

print(
    "AES Algorithm : AES"
)

print(
    "AES Mode      : ECB"
)

print(
    "AES Key       :",
    KEY.decode()
)

print(
    "\nClient ready."
)


# ============================================================
# AUTOMATIC RECEIVE THREAD
# ============================================================

receiver = threading.Thread(
    target=automatic_receiver,
    args=(client,),
    daemon=True
)

receiver.start()


# ============================================================
# CLIENT MENU
# ============================================================

while True:

    print("\n")
    print("=" * 70)
    print("CLIENT MENU")
    print("=" * 70)

    print(
        "1. Encrypt and Send File to Server"
    )

    print(
        "2. Wait / Receive File from Server"
    )

    print(
        "3. Exit"
    )

    print("=" * 70)

    try:

        choice = input(
            "Enter client choice: "
        ).strip()

    except KeyboardInterrupt:

        break

    if choice == "1":

        send_file(
            client
        )

    elif choice == "2":

        print(
            "\nClient is already automatically listening."
        )

        print(
            "Waiting for a file from Server..."
        )

    elif choice == "3":

        try:

            send_string(
                client,
                "EXIT"
            )

        except:
            pass

        print(
            "\nClient stopped."
        )

        break

    else:

        print(
            "\nInvalid choice. Enter 1, 2 or 3."
        )


try:
    client.close()
except:
    pass