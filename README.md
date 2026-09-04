AES-256-CBC FILE TRANSFER

Information Assurance and Security - ALM-2

Name: B.V.LAXMANA
Roll Number: 2420090064
Section: 11

This file is created as the input plaintext for an AES-based
secure file transfer experiment.

In this experiment, the server reads this plaintext file and
encrypts its contents using the AES-256-CBC encryption algorithm.
The encrypted ciphertext is then transferred from the server
to the client through a socket connection.

After receiving the encrypted file, the client uses the same
AES-256 secret key and initialization vector to decrypt the
ciphertext. The original plaintext is then recovered and
displayed on the client side.

The purpose of this experiment is to demonstrate how symmetric
encryption can be used to protect data during file transfer.

PyCryptodome is used for implementing AES encryption and
decryption in Python.

Experiment Result:
The plaintext is successfully encrypted at the server,
transferred as ciphertext, and decrypted successfully at
the client.
