import base64
import os
import yaml

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

vault = {}


def unlock(key):
    global vault
    vault_key_path = os.path.join(__path__[0], 'vault_key.key')
    vault_file_path = os.path.join(__path__[0], 'vault.bin')

    base_f = Fernet(get_base_key(key))
    if not os.path.isfile(vault_key_path):
        raise Exception('The key file is not available')
    with open(vault_key_path, "rb") as key_file:
        double_key = base_f.decrypt(key_file.read())

    double_f = Fernet(double_key)
    with open(vault_file_path, "rb") as vault_file:
        vault = yaml.safe_load(double_f.decrypt(vault_file.read()))


def get_base_key(key):
    salt = b'\x8dy\xcd\xf3\x1a\xec\xc1n\x94\x12\x82\x9d\xf8\xa1&='
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(key.encode('utf-8')))


def prepare(key, old_key=None, force_keyfile_reset=False):
    """
    On the local instance, generates a key file, encrypts that using the passed key,
    and writes the result to this directory. It also encrypts the file vault_base.yaml
    (containing the unencrypted vault content on my dev machine) and stores the resulting
    vault along with the encrypted key file.

    :param key: the key to be used to encrypt everything
    :param old_key: the old key that the key file was encrypted with, if applicable
    :param force_keyfile_reset: if this is True, never try to read the existing key file; always generate a new one.
    """
    vault_key_path = os.path.join(__path__[0], 'vault_key.key')
    vault_base_path = os.path.join(__path__[0], 'vault_base.yaml')
    vault_file_path = os.path.join(__path__[0], 'vault.bin')

    base_f = Fernet(get_base_key(old_key or key))

    # obtain or generate the key file (using an old secret key if necessary)
    if not force_keyfile_reset and os.path.isfile(vault_key_path):
        with open(vault_key_path, "rb") as key_file:
            double_key = base_f.decrypt(key_file.read())
    else:
        double_key = Fernet.generate_key()

    if old_key != key:
        base_f = Fernet(get_base_key(key))
    with open(vault_key_path, "wb") as key_file:
        key_file.write(base_f.encrypt(double_key))

    double_f = Fernet(double_key)

    with open(vault_base_path, "rb") as base_file, open(vault_file_path, "wb") as vault_file:
        vault_file.write(double_f.encrypt(base_file.read()))
