import socket
import threading
import json
import base64
import os
import sys
import hashlib
import getpass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Та же соль, что на сервере (для проверки пароля)
SALT = b"crew_salt977"

LOGO = r"""
          ■■■■■■■■■
        ■■■■■■■■■■■■■
      ■■■■■■■■■■■■■■■■■
    ■■■■■■■■■■■■■■■■■■■■■
  ■■■■■■■■■■     ■■■■■■■■■■
 ■■■■■■■■■         ■■■■■■■■■
■■■■■■■■■           ■■■■■■■■■
 ■■■■■■■             ■■■■■■■
  ■■■■■■               ■■■■■
    ■■■                 ■■■
      ■■■■■■■■■■■■■■■■■■■
        ■■■■■■■■■■■■■■■
          ■■■■■■■■■■■
        ■■■■■■■■■■■■■■■
      ■■■■■■■■   ■■■■■■■■
    ■■■■■■■■       ■■■■■■■■
  ■■■■■■■■           ■■■■■■■■
 ■■■■■■■■             ■■■■■■■■
■■■■■■■■               ■■■■■■■■
■■■■■■■                 ■■■■■■■■
 ■■■■■                   ■■■■■
  ■■■                     ■■■
"""


def print_welcome():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[91m" + LOGO + "\033[0m")
    print("\033[95m" + "=" * 45 + "\033[0m")
    print("\033[95m   ДОБРО ПОЖАЛОВАТЬ В ЗАЩИЩЕННЫЙ МЕССЕНДЖЕР!\033[0m")
    print("\033[95m" + "=" * 45 + "\033[0m\n")


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(password.encode())


def hash_for_server(password: str) -> str:
    return hashlib.sha256(SALT + password.encode()).hexdigest()


# Глобальное состояние
HOST = ""
PORT = 9999
NICK = ""
passwords = {}
current_chat = None
sock = None


def encrypt(chat_id: int, text: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(passwords[chat_id], salt)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, text.encode(), None)
    return base64.b64encode(salt + nonce + ct) + b"\n"


def decrypt(chat_id: int, b64_data: bytes) -> str:
    payload = base64.b64decode(b64_data)
    salt, nonce, ct = payload[:16], payload[16:28], payload[28:]
    key = derive_key(passwords[chat_id], salt)
    return AESGCM(key).decrypt(nonce, ct, None).decode()


def receive_loop():
    buffer = b""
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[!] Соединение закрыто сервером.")
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    text = decrypt(current_chat, line)
                    print(f"\n[чат #{current_chat}] {text}")
                    print("Вы: ", end="", flush=True)
                except Exception:
                    print("\n[!] Не удалось расшифровать (неверный пароль?)")
        except Exception:
            break


def connect_and_auth(chat_id: int, password: str) -> bool:
    global sock
    if sock:
        try:
            sock.close()
        except Exception:
            pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except Exception as e:
        print(f"[!] Не удалось подключиться к серверу: {e}")
        return False

    reg = json.dumps({
        "chat": chat_id,
        "nick": NICK,
        "hash": hash_for_server(password),
    }).encode() + b"\n"
    sock.sendall(reg)

    buffer = b""
    while b"\n" not in buffer:
        data = sock.recv(4096)
        if not data:
            return False
        buffer += data
    line, _ = buffer.split(b"\n", 1)
    try:
        resp = json.loads(line.decode())
    except Exception:
        print("[!] Некорректный ответ сервера.")
        return False

    if resp.get("error") == "bad_password":
        print("\n[!] Неверный пароль. Доступ запрещён.")
        sock.close()
        sock = None
        return False

    if resp.get("ok"):
        passwords[chat_id] = password
        threading.Thread(target=receive_loop, daemon=True).start()
        return True

    return False


def chat_loop():
    print("Введите сообщение (или /menu для выхода из чата):")
    while True:
        msg = input("Вы: ")
        if msg.strip() == "/menu":
            return
        if not msg.strip():
            continue
        try:
            sock.sendall(encrypt(current_chat, f"{NICK}: {msg}"))
        except Exception as e:
            print(f"[!] Ошибка отправки: {e}")
            return


def enter_chat(chat_id: int):
    global current_chat
    try:
        pwd = getpass.getpass(f"Введите пароль для чата #{chat_id}: ").strip()
    except Exception:
        pwd = input(f"Введите пароль для чата #{chat_id}: ").strip()
    if not pwd:
        print("Пустой пароль недопустим.")
        return
    if connect_and_auth(chat_id, pwd):
        current_chat = chat_id
        print(f"\n--- Вы в чате #{chat_id}. ---")
        chat_loop()
        # После выхода из чата вернёмся в меню
        current_chat = None


def menu():
    while True:
        print("\n=== МЕНЮ ЧАТОВ ===")
        for i in range(1, 6):
            mark = " <-- вы здесь" if current_chat == i else ""
            print(f"  {i}. Чат #{i}{mark}")
        print("  0. Выйти")
        choice = input("Выберите чат: ").strip().lower()
        if choice == "0":
            sys.exit(0)
        if choice in {"1", "2", "3", "4", "5"}:
            enter_chat(int(choice))
        else:
            print("Неверный выбор.")


def main():
    global HOST, NICK
    print_welcome()
    HOST = input("Введите IP хоста (Radmin VPN): ").strip()
    NICK = input("Ваш ник: ").strip() or "anon"
    menu()


if __name__ == "__main__":
    main()