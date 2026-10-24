import socket
import threading
import json
import hashlib
import sys

HOST = '0.0.0.0'
PORT = 9999

# --- ПАРОЛИ ЧАТОВ (заданы жёстко на сервере) ---
CHAT_PASSWORDS = {
    1: "CROWDR116178RAW",
    2: "MONJI9901312",
    3: "FRTY124ERTF",
    4: "HJIK66UYT",
    5: "OPLK77DER5",
}

# Фиксированная соль для хеширования паролей (должна совпадать с client.py)
SALT = b"crew_salt977"

# Хеши паролей (вычисляются при старте сервера)
CHAT_HASHES = {
    cid: hashlib.sha256(SALT + pwd.encode()).hexdigest()
    for cid, pwd in CHAT_PASSWORDS.items()
}

clients = {}  # { conn: {"chat": 1, "nick": "...", "ip": "..."} }
lock = threading.Lock()


def check_password(chat_id: int, client_hash: str) -> bool:
    return CHAT_HASHES.get(chat_id) == client_hash


def broadcast(chat_id, message_bytes, sender_conn):
    """Пересылает зашифрованное сообщение всем в том же чате, кроме отправителя."""
    with lock:
        targets = [c for c, info in clients.items()
                   if info["chat"] == chat_id and c is not sender_conn]
    for t in targets:
        try:
            t.sendall(message_bytes)
        except Exception:
            pass


def handle_client(conn, addr):
    buffer = b""
    nick = "anon"
    try:
        # 1. Ждём запрос на аутентификацию: {"chat": 1, "nick": "...", "hash": "..."}
        while b"\n" not in buffer:
            data = conn.recv(4096)
            if not data:
                return
            buffer += data
        line, buffer = buffer.split(b"\n", 1)
        info = json.loads(line.decode())
        chat_id = int(info["chat"])
        nick = info.get("nick", "anon")
        client_hash = info.get("hash", "")

        # 2. Проверяем пароль
        if not check_password(chat_id, client_hash):
            conn.sendall(b'{"error": "bad_password"}\n')
            print(f"\n[!] {nick} пытался войти в чат #{chat_id} с неверным паролем.")
            conn.close()
            return

        conn.sendall(b'{"ok": true}\n')
        client_ip = addr[0]  # Виртуальный IP из Radmin VPN
        with lock:
            clients[conn] = {"chat": chat_id, "nick": nick, "ip": client_ip}
        print(f"\n[+] {nick} вошёл в чат #{chat_id} (IP: {client_ip})")

        # 3. Пересылаем сообщения между клиентами чата
        while True:
            data = conn.recv(4096)
            if not data:
                break
            broadcast(chat_id, data, conn)
            
    except Exception as e:
        print(f"\n[!] Ошибка с {nick}: {e}")
    finally:
        with lock:
            clients.pop(conn, None)
        conn.close()
        if nick != "anon":
            print(f"\n[-] {nick} отключился")


def command_loop():
    """Читает команды с клавиатуры сервера в отдельном потоке."""
    while True:
        try:
            cmd = input().strip()
        except EOFError:
            break
        low = cmd.lower()

        if low == "ips":
            with lock:
                if not clients:
                    print("\n[Сервер] Нет подключённых пользователей.")
                else:
                    print("\n[Сервер] Подключённые пользователи:")
                    for conn, info in clients.items():
                        print(f"  {info['nick']} - {info['ip']} (чат #{info['chat']})")
                        
        elif low == "myips":
            try:
                import psutil
                print("\n[Сервер] IP-адреса этого компьютера:")
                found = False
                for iface, addrs in psutil.net_if_addrs().items():
                    for a in addrs:
                        if a.family == socket.AF_INET:
                            print(f"  {iface}: {a.address}")
                            found = True
                if not found:
                    print("  Не удалось найти IPv4-адреса.")
            except ImportError:
                print("\n[Сервер] Установите psutil: pip install psutil")
                
        elif low.startswith("kick_us"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                print("\n[Сервер] Использование: kick_us <ник>")
                continue
            target_nick = parts[1]
            kicked = False
            with lock:
                for conn, info in list(clients.items()):
                    if info["nick"] == target_nick:
                        try:
                            conn.close()
                        except Exception:
                            pass
                        del clients[conn]
                        print(f"\n[Сервер] Пользователь {target_nick} кикнут.")
                        kicked = True
                        break
            if not kicked:
                print(f"\n[Сервер] Пользователь {target_nick} не найден.")
                
        elif low.startswith("setpass"):
            # setpass <номер> <новый_пароль>
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                print("\n[Сервер] Использование: setpass <1-5> <новый_пароль>")
                continue
            try:
                cid = int(parts[1])
            except ValueError:
                print("\n[Сервер] Номер чата должен быть числом 1-5.")
                continue
            if cid not in CHAT_PASSWORDS:
                print("\n[Сервер] Такого чата нет (только 1-5).")
                continue
            new_pwd = parts[2]
            CHAT_PASSWORDS[cid] = new_pwd
            CHAT_HASHES[cid] = hashlib.sha256(SALT + new_pwd.encode()).hexdigest()
            print(f"\n[Сервер] Пароль чата #{cid} обновлён.")
            
        elif low == "real_ips":
            print("\n[Сервер] Radmin VPN скрывает реальные IP. Видны только 26.x.x.x.")
            
        elif low == "help":
            print("\n[Сервер] Команды:")
            print("  ips                    — показать Ник - IP всех подключённых")
            print("  myips                  — показать IP-адреса этого компьютера")
            print("  kick_us <ник>          — отключить пользователя")
            print("  setpass <1-5> <пароль> — сменить пароль чата")
            print("  real_ips               — объяснение про реальные IP")
            print("  help                   — эта справка")
            
        elif low == "":
            continue
        else:
            print(f"\n[Сервер] Неизвестная команда: {cmd}. Введите 'help'.")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    
    print(f"Сервер запущен на порту {PORT}.")
    print("Введите 'help' для списка команд.")

    # Запускаем поток для чтения команд сервера
    threading.Thread(target=command_loop, daemon=True).start()

    # Основной цикл принятия подключений
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()