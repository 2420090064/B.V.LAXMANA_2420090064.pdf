import socket
import struct
import threading
import os
import io

from Crypto.Cipher import DES
from Crypto.Random import get_random_bytes
from pypdf import PdfReader
from docx import Document


# ============================================================
# SERVER SETTINGS
# ============================================================

HOST = "0.0.0.0"
PORT = 5000

DES_KEY = b"12345678"
BLOCK_SIZE = DES.block_size


# ============================================================
# DES ENCRYPTION CLASS
# ============================================================

class DESManager:

    def __init__(self, key):
        self.key = key

    def add_padding(self, data):

        amount = BLOCK_SIZE - (len(data) % BLOCK_SIZE)

        return data + bytes([amount]) * amount

    def remove_padding(self, data):

        if not data:
            raise ValueError("Empty decrypted data")

        amount = data[-1]

        if amount < 1 or amount > BLOCK_SIZE:
            raise ValueError("Invalid padding")

        if data[-amount:] != bytes([amount]) * amount:
            raise ValueError("Invalid padding")

        return data[:-amount]

    def encrypt(self, data):

        iv = get_random_bytes(BLOCK_SIZE)

        cipher = DES.new(
            self.key,
            DES.MODE_CBC,
            iv
        )

        encrypted = cipher.encrypt(
            self.add_padding(data)
        )

        return iv + encrypted

    def decrypt(self, data):

        if len(data) < BLOCK_SIZE:
            raise ValueError("Invalid encrypted data")

        iv = data[:BLOCK_SIZE]
        encrypted = data[BLOCK_SIZE:]

        cipher = DES.new(
            self.key,
            DES.MODE_CBC,
            iv
        )

        decrypted = cipher.decrypt(encrypted)

        return self.remove_padding(decrypted)


# ============================================================
# SOCKET PROTOCOL
# ============================================================

class NetworkProtocol:

    @staticmethod
    def receive_exact(sock, number):

        buffer = bytearray()

        while len(buffer) < number:

            chunk = sock.recv(
                min(65536, number - len(buffer))
            )

            if not chunk:
                raise ConnectionError(
                    "Remote connection closed."
                )

            buffer.extend(chunk)

        return bytes(buffer)

    @staticmethod
    def send_bytes(sock, data):

        header = struct.pack(
            "!Q",
            len(data)
        )

        sock.sendall(header)
        sock.sendall(data)

    @staticmethod
    def receive_bytes(sock):

        header = NetworkProtocol.receive_exact(
            sock,
            8
        )

        length = struct.unpack(
            "!Q",
            header
        )[0]

        return NetworkProtocol.receive_exact(
            sock,
            length
        )

    @staticmethod
    def send_text(sock, text):

        NetworkProtocol.send_bytes(
            sock,
            text.encode("utf-8")
        )

    @staticmethod
    def receive_text(sock):

        data = NetworkProtocol.receive_bytes(sock)

        return data.decode("utf-8")


# ============================================================
# FILE CONTENT READER
# ============================================================

def extract_text(filename, data):

    extension = os.path.splitext(
        filename
    )[1].lower()

    # --------------------------------------------------------
    # TEXT FILES
    # --------------------------------------------------------

    if extension in [
        ".txt",
        ".csv",
        ".py",
        ".c",
        ".cpp",
        ".java",
        ".html",
        ".css"
    ]:

        return data.decode(
            "utf-8",
            errors="replace"
        )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if extension == ".pdf":

        try:

            reader = PdfReader(
                io.BytesIO(data)
            )

            pages = []

            for page in reader.pages:

                text = page.extract_text()

                if text:
                    pages.append(text)

            result = "\n".join(pages)

            if result.strip():
                return result

            return "[No readable text found in PDF]"

        except Exception as error:

            return f"[PDF extraction error: {error}]"

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if extension == ".docx":

        try:

            document = Document(
                io.BytesIO(data)
            )

            paragraphs = []

            for paragraph in document.paragraphs:
                paragraphs.append(paragraph.text)

            result = "\n".join(paragraphs)

            if result.strip():
                return result

            return "[No readable text found in DOCX]"

        except Exception as error:

            return f"[DOCX extraction error: {error}]"

    # --------------------------------------------------------
    # BINARY
    # --------------------------------------------------------

    return None


# ============================================================
# SERVER CLASS
# ============================================================

class DESFileServer:

    def __init__(self):

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.crypto = DESManager(
            DES_KEY
        )

        self.client = None
        self.running = True

    # --------------------------------------------------------
    # START SERVER
    # --------------------------------------------------------

    def start(self):

        self.socket.bind(
            (HOST, PORT)
        )

        self.socket.listen(1)

        self.print_header()

        print("\nWaiting for client connection...")

        self.client, address = self.socket.accept()

        print("\nClient connected!")
        print("Client IP   :", address[0])
        print("Client Port :", address[1])

        print("\nDES Key     :", DES_KEY.decode())
        print("Encryption  : DES CBC")

        listener = threading.Thread(
            target=self.listen,
            daemon=True
        )

        listener.start()

        self.menu()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def print_header(self):

        print("\n" + "=" * 65)
        print("             DES SECURE FILE SERVER")
        print("=" * 65)
        print("Host :", HOST)
        print("Port :", PORT)
        print("=" * 65)

    # --------------------------------------------------------
    # LISTEN FOR CLIENT
    # --------------------------------------------------------

    def listen(self):

        while self.running:

            try:

                command = NetworkProtocol.receive_text(
                    self.client
                )

                if command == "SEND_FILE":

                    self.receive_file()

                elif command == "EXIT":

                    print(
                        "\nClient closed the connection."
                    )

                    self.running = False
                    break

                else:

                    print(
                        "\nUnknown command:",
                        command
                    )

            except Exception as error:

                if self.running:

                    print(
                        "\nClient connection error:",
                        error
                    )

                break

    # --------------------------------------------------------
    # RECEIVE FILE
    # --------------------------------------------------------

    def receive_file(self):

        try:

            filename = NetworkProtocol.receive_text(
                self.client
            )

            encrypted = NetworkProtocol.receive_bytes(
                self.client
            )

            print("\n" + "=" * 65)
            print("          ENCRYPTED FILE RECEIVED")
            print("=" * 65)

            print("File name        :", filename)
            print(
                "Ciphertext size  :",
                len(encrypted),
                "bytes"
            )

            plaintext = self.crypto.decrypt(
                encrypted
            )

            print(
                "Plaintext size   :",
                len(plaintext),
                "bytes"
            )

            print("\nDecryption successful.")

            self.show_content(
                filename,
                plaintext
            )

            print("=" * 65)

        except Exception as error:

            print(
                "\nUnable to receive file:",
                error
            )

    # --------------------------------------------------------
    # SEND FILE
    # --------------------------------------------------------

    def send_file(self):

        path = input(
            "\nEnter complete file path: "
        ).strip()

        if not os.path.isfile(path):

            print("\nFile does not exist.")

            return

        try:

            with open(path, "rb") as file:

                plaintext = file.read()

            filename = os.path.basename(path)

            print("\nFile selected :", filename)
            print(
                "Original size :",
                len(plaintext),
                "bytes"
            )

            print("\nEncrypting...")

            encrypted = self.crypto.encrypt(
                plaintext
            )

            NetworkProtocol.send_text(
                self.client,
                "SEND_FILE"
            )

            NetworkProtocol.send_text(
                self.client,
                filename
            )

            NetworkProtocol.send_bytes(
                self.client,
                encrypted
            )

            print("\nFile sent successfully.")

            print(
                "Encrypted size:",
                len(encrypted),
                "bytes"
            )

            self.show_content(
                filename,
                plaintext
            )

        except Exception as error:

            print(
                "\nFile transfer failed:",
                error
            )

    # --------------------------------------------------------
    # SHOW FILE CONTENT
    # --------------------------------------------------------

    def show_content(self, filename, data):

        readable = extract_text(
            filename,
            data
        )

        print("\n----- PLAINTEXT CONTENT -----")

        if readable is not None:

            if len(readable) > 4000:

                print(
                    readable[:4000]
                )

                print(
                    "\n...[content truncated]..."
                )

            else:

                print(readable)

        else:

            print(
                "Binary file detected."
            )

            print(
                "First 200 bytes:"
            )

            print(
                data[:200].hex()
            )

        print("\n----- CIPHERTEXT PREVIEW -----")

        encrypted_preview = self.crypto.encrypt(
            data
        )

        print(
            encrypted_preview[:200].hex()
        )

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    def menu(self):

        while self.running:

            print("\n")
            print("=" * 65)
            print("                    SERVER MENU")
            print("=" * 65)
            print("1. Encrypt and Send File")
            print("2. Receive and Decrypt File")
            print("3. Exit")
            print("=" * 65)

            option = input(
                "Select option: "
            ).strip()

            if option == "1":

                self.send_file()

            elif option == "2":

                print(
                    "\nWaiting for the client to send a file..."
                )

                print(
                    "Use the SEND FILE option on the client."
                )

                input(
                    "\nPress ENTER to return to menu..."
                )

            elif option == "3":

                self.stop()

            else:

                print(
                    "\nInvalid option."
                )

    # --------------------------------------------------------
    # STOP SERVER
    # --------------------------------------------------------

    def stop(self):

        print("\nClosing server...")

        self.running = False

        try:

            NetworkProtocol.send_text(
                self.client,
                "EXIT"
            )

        except:
            pass

        try:
            self.client.shutdown(
                socket.SHUT_RDWR
            )
        except:
            pass

        try:
            self.client.close()
        except:
            pass

        try:
            self.socket.close()
        except:
            pass

        print("Server stopped.")


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    try:

        application = DESFileServer()

        application.start()

    except KeyboardInterrupt:

        print("\n\nServer interrupted.")

    except Exception as error:

        print(
            "\nServer error:",
            error
        )