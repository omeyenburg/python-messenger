#! /usr/bin/env python
# -*- encoding: utf-8 -*-
from datetime import datetime
import sqlite3
import tkinter
import socket
import time
import sys
import os


ECHO_PORT = 50007


class Server:
    def __init__(self, db_file):
        self.running = True
        self.BUFSIZE = 1024

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.bind(("", ECHO_PORT))
        self.soc.settimeout(0.1)
        self.soc.listen(1)
        self.connections = []
        self.db_file = db_file

        try:
            if os.path.split(os.getcwd())[-1] != "server":
                os.chdir("./server")
        except:
            pass

        self.database = sqlite3.connect(self.db_file)
        self.cursor = self.database.cursor()

        try:
            self.cursor.execute("SELECT * FROM accounts")
            self.cursor.fetchall()
        except:
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS accounts (username text PRIMARY KEY, password text NOT NULL, description text)"
            )
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS messages (id integer PRIMARY KEY, content text NOT NULL, time text NOT NULL, sender text NOT NULL, receiver text NOT NULL)"
            )

        self.news = []

    def connect(self):
        try:
            connection, (remotehost, remoteport) = self.soc.accept()
        except socket.timeout:
            pass
        else:
            connection.setblocking(False)
            self.connections.append([connection, remotehost, remoteport, "", 0, {}])

    def update(self, window):
        for i, (
            connection,
            remotehost,
            remoteport,
            username,
            public,
            private,
        ) in enumerate(self.connections):
            try:
                data = connection.recv(self.BUFSIZE)
            except BlockingIOError:
                continue

            data = data.decode()
            if not data:
                self._disconnect(i, "")
                continue

            answer = {
                "0": self._disconnect,
                "1": self._log_in,
                "2": self._log_out,
                "3": self._create_account,
                "4": self._modify_account,
                "5": self._update,
                "6": self._retrieve_message,
                "7": self._retrieve_accounts,
                "8": self._send_message,
            }[data[0]](i, data[1:])

            if data[0] != "0":
                connection.send(answer.encode())

        if not self.running:
            self.quit()
            return

        self.connect()

        window.after(1, self.update, window)

    def _disconnect(self, i, data):
        self.connections[i][0].shutdown(1)
        self.connections.pop(i)
        return ""

    def _log_in(self, i, data):
        connection, remotehost, remoteport, username, public, private = (
            self.connections[i]
        )
        username, password = data.split("%", 1)
        self.cursor.execute(
            f'SELECT * FROM accounts WHERE username = "{username}" AND password = "{password}"'
        )
        if len(self.cursor.fetchall()) != 1:
            return "deny%Benutzername oder Passwort falsch."
        self.connections[i][3] = username
        return "accept"

    def _log_out(self, i, data):
        self.connections[i][3] = ""
        return "received"

    def _create_account(self, i, data):
        username, password = data.split("%", 1)
        if not len(username):
            return "deny%Benutzername zu kurz"
        elif not len(password):
            return "deny%Passwort zu kurz."
        for char in username:
            if (
                not char
                in "0123456789 _ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            ):
                return "deny%Benutzernamen können nur aus Zahlen, Buchstaben, Leerzeichen und Unterstrichen bestehen."
        try:
            self.cursor.execute(
                f'INSERT INTO accounts VALUES ("{username}", "{password}", "")'
            )
            self.database.commit()
            self.news.append((username, ""))
        except socket.timeout:
            return "deny%Benutzername existiert bereits."
        self.connections[i][3] = username
        return "accept"

    def _modify_account(self, i, data):
        description = data
        username = self.connections[i][3]
        self.cursor.execute(
            f'UPDATE accounts SET description = "{description}" WHERE username = "{self.connections[i][3]}"'
        )
        self.database.commit()
        self.news.append((self.connections[i][3], description))
        return "received"

    def _update(self, i, data):
        connection, remotehost, remoteport, username, public, private = (
            self.connections[i]
        )
        data = []
        for username, description in self.news[self.connections[i][4] :]:
            if username in private:
                message_num = private[username]
                private.pop(username)
            else:
                message_num = 0
            data.append(
                username
                + "%1%"
                + str(message_num)
                + "%"
                + str(len(description))
                + "%"
                + description
            )
        for username, message_num in private.items():
            data.append(username + "%0%" + str(message_num) + "%")
        answer = "%".join(data)
        self.connections[i][4] = len(self.news)
        self.connections[i][5] = {}
        return "%" + answer

    def _retrieve_message(self, i, data):
        chat, time, num = data.split("%")
        username = self.connections[i][3]

        if time == "before":
            modifier = ("MAX", "<")
        else:
            modifier = ("MIN", ">")
        if int(num) >= 0:
            request = f'SELECT * FROM messages WHERE id = (SELECT {modifier[0]}(id) FROM messages WHERE id {modifier[1]} {num} AND (receiver = "{chat}" AND sender = "{username}" OR receiver = "{username}" AND sender = "{chat}"))'
        else:
            request = f'SELECT * FROM messages WHERE id = (SELECT {modifier[0]}(id) FROM messages WHERE receiver = "{chat}" AND sender = "{username}" OR receiver = "{username}" AND sender = "{chat}")'
        self.cursor.execute(request)

        result = self.cursor.fetchone()
        if result is None:
            return "None"
        message_id, content, time, sender, receiver = result
        return str(message_id) + "%" + time + "%" + sender + "%" + content

    def _retrieve_accounts(self, i, data):
        self.cursor.execute("SELECT username, description FROM accounts")
        return "%" + "%".join(["%".join(i) for i in self.cursor.fetchall()])

    def _send_message(self, i, data):
        receiver, content = data.split("%", 1)
        sender = self.connections[i][3]
        self.cursor.execute("SELECT MAX(id) FROM messages")
        message_id = self.cursor.fetchall()[0][0]
        if message_id is None:
            message_id = 1
        else:
            message_id += 1
        time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        query = "INSERT INTO messages VALUES (?, ?, ?, ?, ?)"
        values = (message_id, content, time, sender, receiver)
        self.cursor.execute(query, values)
        self.database.commit()
        self.connections[i][5][sender] = self.connections[i][5].get(sender, 0) + 1
        for i in range(len(self.connections)):
            if self.connections[i][3] == receiver:
                self.connections[i][5][sender] = (
                    self.connections[i][5].get(sender, 0) + 1
                )
        return "received"

    def quit(self, event):
        if repr(event.widget) == ".":
            self.cursor.close()
            self.database.close()
            self.soc.close()


def get_db_file():
    if "--database" in sys.argv:
        index = sys.argv.index("--database") + 1
        if index < len(sys.argv):
            cwd = os.getcwd()
            return os.path.join(cwd, sys.argv[index])

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(script_dir, os.path.pardir, "data", "server.db")


def main():
    db_file = get_db_file()
    server = Server(db_file)

    window = tkinter.Tk()
    window.title("Server")
    window.geometry("150x30")
    window.bind("<Destroy>", server.quit)

    tkinter.Button(window, text="stop", command=window.destroy).pack()
    window.after(1, server.update, window)

    window.mainloop()


main()
