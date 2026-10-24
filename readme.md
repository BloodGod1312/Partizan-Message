# 🔐 Partizan Message by LNO

**Анонимный** мессенджер на **Python** с шифрованием **AES-256-GCM**, работающий поверх виртуальной сети **Radmin VPN**. **Без центральных серверов, без регистрации** — только ник, IP хоста и пароль от чата.

![Логотип](https://img.shields.io/badge/secure-AES--256--GCM-brightgreen)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
[![Donate](https://img.shields.io/badge/Donate-DonationAlerts-ff69b4?style=for-the-badge&logo=ko-fi)](https://www.donationalerts.com/r/mr_fill_bg)

## ✨ Возможности

- 🔒 **Сквозное шифрование** сообщений (AES-256-GCM, PBKDF2 с 200 000 итераций)
- 🗂 **5 независимых чатов**, каждый со своим паролем, которые устанавливает сервер
- 🎭 **Минимальная регистрация** — только ник и пароль от чата
- 🖥 **Серверное меню**: список клиентов, кик, смена паролей
- 🌐 **Работает без публичного IP** — поверх Radmin VPN
- 🆓 **Полностью бесплатно** и с открытым исходным кодом и без возможности попасть под запрет или белые списки

## ❓ FAQ:
- Как подключиться к чату?
Вам нужно указать в коде client.py соль (salt), указанную в коде server.py (по дефолту crew_salt977) и пароль при выборе чата (к каждому чату - свой пароль), который также устанавливает сервер. Дефолтные пароли указаны в server.py в строке CHAT_PASSWORDS

- Какой IP давать серверу клиентам? 
Нужно давать IP от Radmin, который вам выдаст команда myips . Другие IP просто нужны для справки.

- Как увидеть РЕАЛЬНЫЕ IP моих пользователей? 
Никак, команда real_ips в подробностях объяснит почему.

- Сохраняется ли история чата?
Нет, история чата нигде не хранится, при закрытие терминала история чата на вашем компьютере стирается

## 📋 Требования

- [Python 3.8+](https://www.python.org/downloads/) (при установке отметьте галочку **Add Python to PATH**)
- [Radmin VPN](https://www.radmin-vpn.com/) (для связи между компьютерами)
- [Git](https://git-scm.com/downloads) (для установки через `git clone`)

## 📥 Установка через git clone

### Вариант 1: Клонирование через Git (рекомендуется)

Откройте терминал (Git Bash, PowerShell или командную строку) и выполните:

```bash
# 1. Клонируем репозиторий
git clone https://github.com/BloodGod1312/Partizan-Message.git

# 2. Переходим в папку проекта
cd Partizan-Message

# 3. Устанавливаем зависимости
pip install cryptography psutil (если не работает, то python -m pip install cryptography psutil)
