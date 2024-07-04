#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os

import socket
from tkinter import font as tkfont
from tkinter import *


STANDARD_BUFFER_SIZE = 1024
SENDER_SELF_NAME = "You"

TEXTS_EN = {
    "connection_failed": "Connection to server failed.",
    "connection_aborted": "Connection aborted.",
    "log_in": "Log in",
    "create_account": "Create Account",
    "username": "Username",
    "password": "Password",
    "stay_logged_in": "Stay logged in",
    "password_warning": "Don't use a real password!",
    "no_server_connection": "No connection with server.",
    "wrong_log_in": "Wrong username or password.",
    "short_username": "Username too short.",
    "short_password": "Passoword too short.",
    "illegal_username": "Usernames can only consist of numbers, alphabetic letters, whitespaces and underscores.",
    "profile": "profile",
    "description": "Description",
    "save_description": "Save description",
    "log_out": "log out",
    "settings": "Settings",
    "design": "design",
    "same_pc": "Same PC",
    "server_port": "Server Port",
    "save": "Save",
    "design_restart_info": "Design change requires restart.",
}

TEXTS_DE = {
    "connection_failed": "Verbindung mit Server ist fehlgeschlagen.",
    "connection_aborted": "Verbindung ist abgebrochen.",
    "log_in": "Log in",
    "create_account": "Account erstellen",
    "username": "Benutzername",
    "password": "Passwort",
    "stay_logged_in": "Eingeloggt bleiben",
    "password_warning": "Nutze kein echtes Passwort!",
    "no_server_connection": "Nicht mit Server verbunden.",
    "wrong_log_in": "Benutername oder Passwort falsch.",
    "short_username": "Benutername zu kurz.",
    "short_password": "Passwort zu kurz.",
    "illegal_username": "Benutzernamen können nur aus Zahlen, Buchstaben, Leerzeichen und Unterstrichen bestehen.",
    "profile": "Profil",
    "description": "Beschreibung",
    "save_description": "Beschreibung speichern",
    "log_out": "Ausloggen",
    "settings": "Einstellungen",
    "design": "Design",
    "same_pc": "Gleicher Rechner",
    "server_port": "Server Port",
    "save": "Speichern",
    "design_restart_info": "Designänderungen erfordern einen Programmneustart.",
}

TEXTS = TEXTS_DE


class Client:
    def __init__(self):
        if int(settings["localhost"]):
            settings["ip"] = socket.gethostname()

        self.BUFSIZE = 1024
        self.connected = False

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.settimeout(0.1)

        self.connect()

        self.account_list = []  # username, description, unread_messages
        if self.connected:
            accounts = self.send("retrieve accounts")[1:]
            accounts = accounts.split("%")
            if len(accounts) >= 2:
                for i in range(0, len(accounts), 2):
                    self.account_list.append([*accounts[i : i + 2], 0])

        self.friends = {}

    def connect(self):
        if not self.connected:
            try:
                self.soc.connect((settings["ip"], int(settings["port"])))
            except:
                Page.info(TEXTS["connection_failed"])
                window.connect_button.place(
                    x=window.user_width - window.bar_height * 2,
                    y=-window.bar_height,
                    rely=1,
                    w=window.bar_height,
                    h=window.bar_height,
                )
            else:
                self.connected = True
                window.connect_button.place_forget()

    def send(self, data_type, content=""):
        if self.connected:
            data = self.encode(data_type, content)
            try:
                self.soc.send(data)
            except BrokenPipeError:
                Page.info(TEXTS["connection_aborted"])
                self.connected = False
                return
            self.soc.settimeout(None)
            try:
                answer = self.soc.recv(self.BUFSIZE)
            except ConnectionResetError:
                Page.info(TEXTS["connection_aborted"])
                self.connected = False
                return
            finally:
                self.soc.settimeout(0.1)
            return answer.decode()

    def encode(self, data_type, content=""):
        data = str(
            {
                "disconnect": "0",
                "log in": "1",
                "log out": "2",
                "create account": "3",
                "modify account": "4",
                "update": "5",
                "retrieve message": "6",
                "retrieve accounts": "7",
                "send message": "8",
            }[data_type]
        )

        if (
            data_type == "disconnect"
            or data_type == "log out"
            or data_type == "update account"
        ):
            pass
        elif data_type == "send message":
            data += Page.opened[1:] + "%" + content
        else:
            data += content

        return data.encode()

    def update(self):
        u = self.send("update")

        if not u is None and len(u) > 1:
            length = len(u)
            index = 0
            while 1:
                n = u.find("%", index + 1)
                if n == -1:
                    break
                username = u[index + 1 : n]
                index = n

                n = u.find("%", index + 1)
                modify = int(u[index + 1 : n])
                index = n

                n = u.find("%", index + 1)
                message_num = int(u[index + 1 : n])
                index = n

                if settings["username"] == username:
                    if Page.opened[0] == "%":
                        Page.pages[Page.opened].retrieve_message("after")
                        Page.pages[Page.opened].update()

                if modify:
                    n = u.find("%", index + 1)
                    description_length = int(u[index + 1 : n])
                    index = n

                    n += description_length + 1
                    description = u[index + 1 : n]
                    index = n + 1

                for i, (u, *_) in enumerate(self.account_list):
                    if u == username:
                        if modify:
                            self.account_list[i][1] = description
                        if u != Page.opened[1:]:
                            self.account_list[i][2] += message_num
                        else:
                            Page.pages[Page.opened].retrieve_message("after")
                            Page.pages[Page.opened].update()
                        break
                else:
                    self.account_list.append([username, description, 0])

            window.update_user_list()
        window.window.after(1000, self.update)

    def close(self):
        if self.connected:
            self.send("disconnect")
            self.connected = False
            self.soc.close()


class Window:
    def __init__(self, title):
        self.window = Tk()
        self.window.title(title)
        self.window.bind("<Destroy>", self.close)
        self.root = Frame(self.window, bg=settings["color_bg_bar"])
        self.root.place(relw=1, relh=1)

        screen_width = self.window.winfo_screenwidth()  # Width of the screen
        screen_height = self.window.winfo_screenheight()  # Height of the screen
        settings["font_size"] = str(screen_width / 1500)

        w = screen_width * 2 // 3
        h = screen_height * 3 // 5
        x = (screen_width // 2) - (w // 2)
        y = (screen_height // 2) - (h // 2)
        self.window.geometry("%dx%d+%d+%d" % (w, h, x, y))

        self.user_width = w // 3
        self.bar_height = w // 28
        self.window.minsize(self.user_width, self.bar_height)

        self.user_box = Text(
            self.root,
            bg=settings["color_bg_user"],
            bd=0,
            highlightthickness=0,
            borderwidth=0,
            cursor="arrow",
            fg=settings["color_text"],
        )
        self.user_box.config(state="disabled")
        self.user_box.place(x=-1, y=-1, w=self.user_width, relh=1, h=-self.bar_height)

        profile_button = Label(
            self.root,
            text="\u263A",
            font=settings.font(15),
            bg=settings["color_bg_bar"],
            fg=settings["color_text"],
        )
        profile_button.bind("<Button-1>", lambda _: Page.open("profile"))
        profile_button.place(
            y=-self.bar_height, rely=1, w=self.bar_height, h=self.bar_height
        )

        self.user_label = Label(
            self.root,
            text="",
            font=settings.font(15),
            anchor="w",
            bg=settings["color_bg_bar"],
            fg=settings["color_text"],
        )
        self.user_label.bind("<Button-1>", lambda _: Page.open("profile"))
        self.user_label.place(
            x=self.bar_height, y=-self.bar_height, rely=1, h=self.bar_height
        )

        self.connect_button = Label(
            self.root,
            text="\u27F3",
            font=settings.font(15),
            bg=settings["color_bg_bar"],
            fg=settings["color_text"],
        )
        self.connect_button.bind("<Button-1>", self._connect)
        self.connect_button.place(
            x=self.user_width - self.bar_height * 2,
            y=-self.bar_height,
            rely=1,
            w=self.bar_height,
            h=self.bar_height,
        )
        self.connect_button.place(
            x=self.user_width - self.bar_height * 2,
            y=-self.bar_height,
            rely=1,
            w=self.bar_height,
            h=self.bar_height,
        )

        settings_button = Label(
            self.root,
            text="\u2699",
            font=settings.font(15),
            bg=settings["color_bg_bar"],
            fg=settings["color_text"],
        )
        settings_button.bind("<Button-1>", lambda _: Page.open("settings"))
        settings_button.place(
            x=self.user_width - self.bar_height,
            y=-self.bar_height,
            rely=1,
            w=self.bar_height,
            h=self.bar_height,
        )

    def update_user_list(self):
        if settings["logged_in"] == "1":
            users = tuple(
                sorted(
                    filter(lambda x: x[0] != settings["username"], client.account_list),
                    key=lambda x: client.friends.get(x[0], (0, 0))[1],
                    reverse=True,
                )
            )
        else:
            users = ()

        self.user_box.config(state="normal")
        self.user_box.delete("1.0", END)
        scroll = lambda event: self.user_box.yview_scroll(-event.delta, "units")

        for i, (username, description, unread_messages) in enumerate(users):
            if username == Page.opened[1:]:
                bg = settings["color_text_faded"]
            else:
                bg = (settings["color_bg_faded"], settings["color_bg_user"])[i % 2]
            click = lambda event, username=username: Page.open("%" + username)

            f = Frame(
                self.user_box,
                bg=bg,
                width=self.user_width - 2,
                height=self.bar_height * 1.5,
                bd=0,
            )

            l1 = Label(
                f,
                text=username,
                bg=bg,
                anchor="w",
                font=settings.font(13),
                fg=settings["color_text"],
            )
            l1.place(x=5, y=0, relw=1, relh=0.5)

            l2 = Label(
                f,
                text=description,
                bg=bg,
                anchor="w",
                font=settings.font(12),
                fg=settings["color_text"],
            )
            l2.place(x=5, rely=0.5, relw=1, relh=0.5)

            selected = client.friends.get(username, (0, 0))[1]
            l3 = Label(
                f,
                text="\u2605",
                bg=bg,
                fg=(bg, "#ffcf40")[selected],
                anchor="w",
                font=settings.font(18),
            )
            l3.place(x=-60, relx=1, y=0, relw=1, relh=0.5)
            i = len(client.friends)
            client.friends[username] = [l3, selected, bg]

            message_num = ""
            for u, d, n in client.account_list:
                if username == u:
                    if n:
                        message_num = str(n)
                    break

            l4 = Label(
                f,
                text=str(message_num),
                bg=bg,
                anchor="w",
                font=settings.font(12),
                fg=settings["color_text"],
            )
            l4.place(x=-20, relx=1, y=0, relw=1, relh=0.5)

            for widget in (l1, l2, l3):
                widget.bind("<MouseWheel>", scroll)
                widget.bind("<Button-1>", click)
                widget.bind("<Enter>", lambda _, i=l3: Window.star_hover(i))
                widget.bind("<Leave>", lambda _, bg=bg: Window.star_hover(None))

            l3.bind("<Button-1>", lambda _, u=username: Window.star_click(u))

            self.user_box.window_create(END, window=f)
            if i < len(users) - 1:
                self.user_box.insert(END, "\n")
        self.user_box.config(state="disabled")
        self.user_box.update_idletasks()

    def star_hover(l):
        for i, (star, selected, bg) in client.friends.items():
            if selected or not star.winfo_exists():
                continue
            elif l == star:
                star.config(fg="#916d00")
            else:
                star.config(fg=bg)

    def star_click(i):
        client.friends[i][1] = int(not client.friends[i][1])
        if not client.friends[i][0].winfo_exists():
            return
        if client.friends[i][1]:
            # client.friends[i][0].place(x=-40, relx=1, y=0, relw=1, relh=0.5)
            client.friends[i][0].config(fg="#ffcf40")
        else:
            # client.friends[i][0].place(x=-40, relx=1, y=0, relw=1, relh=0.5)
            client.friends[i][0].config(fg="#916d00")
        window.update_user_list()

    def _connect(self, *args):
        client.connect()

    def _send(self, text):
        client.send("send message", text)

    def close(self, event):
        if event.widget == self.root:
            client.close()

    def start(self):
        self.window.after(100, client.update)
        self.window.mainloop()


class Page:
    opened = ""
    pages = {}
    info_l = None
    info_e = 0
    info_y = 0
    chats = {}

    def __init__(self):
        Page.pages["log in"] = Page.log_in()
        Page.pages["create account"] = Page.create_account()
        Page.pages["profile"] = Page.profile()
        Page.pages["settings"] = Page.settings()

    def info(text=None, t=2000, delta=0.01, color=None):
        if Page.info_l is None:
            Page.info_l = Label(
                window.window,
                bg=settings["color_bg_bar"],
                borderwidth=0,
                highlightcolor=settings["color_text"],
                highlightthickness=0,
            )

        if not text is None:
            t = 50 * len(text)
            if color is None:
                color = settings["color_text"]
            Page.info_l.config(text=text, fg=color)
        Page.info_y = min(0.1, max(0, Page.info_y + delta))
        Page.info_l.place(rely=Page.info_y - 0.1, relx=0.2, relw=0.6, relh=0.1)
        Page.info_l.lift()
        if Page.info_y < 0.1 and delta > 0:
            Page.info_s = Page.info_l.after(1, Page.info, None, t)
            Page.info_s = Page.info_l.after(t, Page.info, None, t, -0.015)

    def log_in():
        root = Frame(window.root, bg=settings["color_bg_main"])
        centered = Frame(root, bg=settings["color_bg_main"])
        centered.pack(padx=30, pady=40, anchor="w")

        Label(
            centered,
            text=TEXTS["log_in"],
            font=settings.font(15),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=0, sticky="w", pady=20)
        l = Label(
            centered,
            text=TEXTS["create_account"],
            fg=settings["color_text_link"],
            font=settings.font(10),
            bg=settings["color_bg_main"],
        )
        l.grid(column=1, row=0, sticky="w")
        l.bind("<Button-1>", lambda _: Page.open("create account"))
        Label(
            centered,
            text=TEXTS["username"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=1, sticky="e", padx=50)
        e1 = Entry(
            centered,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e1.grid(column=1, row=1, sticky="w")
        Label(
            centered,
            text=TEXTS["password"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=2, sticky="e", padx=50)
        e2 = Entry(
            centered,
            font=settings.font(13),
            show="*",
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e2.grid(column=1, row=2, sticky="w", pady=10)
        e1.bind("<Return>", lambda _: e2.focus())
        e3 = IntVar(value=int(settings["stay_logged_in"]))
        Checkbutton(
            centered,
            text=TEXTS["stay_logged_in"],
            font=settings.font(13),
            fg=settings["color_text"],
            variable=e3,
            bg=settings["color_bg_main"],
        ).grid(column=0, row=3, sticky="w", pady=10)
        b = Button(
            centered,
            text=TEXTS["log_in"],
            font=settings.font(13),
            fg=settings["color_text"],
            command=lambda: Page.log_in_action(e1, e2, e3),
            bg=settings["color_bg_faded"],
            highlightbackground=settings["color_bg_faded"],
            highlightcolor=settings["color_bg_faded"],
        )
        b.grid(column=0, row=4, sticky="w")
        e1.bind("<Return>", lambda _: e2.focus())
        e2.bind("<Return>", lambda _: Page.log_in_action(e1, e2, e3))

        return root

    def create_account():
        root = Frame(window.root, bg=settings["color_bg_main"])
        centered = Frame(root, bg=settings["color_bg_main"])
        centered.pack(padx=30, pady=40, anchor="w")

        Label(
            centered,
            text=TEXTS["create_account"],
            font=settings.font(15),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=0, sticky="w", pady=20)
        l = Label(
            centered,
            text=TEXTS["log_in"],
            fg=settings["color_text_link"],
            font=settings.font(10),
            bg=settings["color_bg_main"],
        )
        l.grid(column=1, row=0, sticky="w")
        l.bind("<Button-1>", lambda _: Page.open("log in"))
        Label(
            centered,
            text=TEXTS["username"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=1, sticky="e", padx=50)
        e1 = Entry(
            centered,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e1.grid(column=1, row=1, sticky="w")
        Label(
            centered,
            text=TEXTS["password"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=2, sticky="e", padx=50)
        e2 = Entry(
            centered,
            font=settings.font(13),
            show="*",
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e2.grid(column=1, row=2, sticky="w", pady=10)
        Label(
            centered,
            text=TEXTS["password_warning"],
            font=settings.font(10),
            justify="left",
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=2, row=2, padx=10)
        e3 = IntVar(value=int(settings["stay_logged_in"]))
        c = Checkbutton(
            centered,
            text=TEXTS["stay_logged_in"],
            font=settings.font(13),
            fg=settings["color_text"],
            variable=e3,
            bg=settings["color_bg_main"],
        )
        c.grid(column=0, row=3, sticky="w", pady=10)
        Button(
            centered,
            text=TEXTS["create_account"],
            font=settings.font(13),
            fg=settings["color_text"],
            command=lambda: Page.create_account_action(e1, e2, e3),
            bg=settings["color_bg_faded"],
            highlightbackground=settings["color_bg_faded"],
        ).grid(column=0, row=4, sticky="w")
        e1.bind("<Return>", lambda _: e2.focus())
        e2.bind("<Return>", lambda _: Page.create_account_action(e1, e2, e3))

        return root

    def log_in_action(*args, direct=0):
        if direct:
            username, password = args
        else:
            settings["stay_logged_in"] = str(args[2].get())

            username = args[0].get()
            password = args[1].get()

        if not client.connected:
            Page.info(TEXTS["no_server_connection"])
            return

        answer = client.send("log in", "%".join((username, password))).split("%")

        if answer[0] == "deny":
            Page.info(TEXTS["wrong_log_in"], color="red")
            return

        settings["username"] = username
        settings["password"] = password
        settings["logged_in"] = "1"
        window.user_label.config(text=username)
        Page.open("profile")
        Page.update()

        for i in range(len(client.account_list)):
            client.account_list[i][2] = 0

        window.update_user_list()

    def create_account_action(*args):
        settings["stay_logged_in"] = str(args[2].get())

        username = args[0].get()
        password = args[1].get()

        if not client.connected:
            Page.info(TEXTS["no_server_connection"])
            return
        if not len(username):
            Page.info(TEXTS["short_username"])
            return
        elif not len(password):
            Page.info(TEXTS["short_password"])
            return
        for char in username:
            if (
                not char
                in "0123456789 _ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            ):
                Page.info(
                    TEXTS["illegal_username"]
                )
                return

        answer = client.send("create account", "%".join((username, password))).split(
            "%"
        )

        if answer[0] == "deny":
            Page.info(answer[1], color="red")
            return

        settings["username"] = username
        settings["password"] = password
        settings["logged_in"] = "1"
        window.user_label.config(text=username)
        Page.open("profile")
        Page.update()

        for i in range(len(client.account_list)):
            client.account_list[i][2] = 0

        window.update_user_list()

    def update():
        Page.user_label.config(text=settings["username"])
        Page.description_entry.delete(0, END)
        for u, d, n in client.account_list:
            if u == settings["username"]:
                Page.description_entry.insert(END, d)
                break

    def profile():
        root = Frame(window.root, bg=settings["color_bg_main"])
        centered = Frame(root, bg=settings["color_bg_main"])
        centered.pack(padx=30, pady=40, anchor="w")

        Label(
            centered,
            text=TEXTS["profile"],
            font=settings.font(15),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=0, sticky="w", pady=20)
        Label(
            centered,
            text=TEXTS["username"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=1, sticky="e", padx=50)
        Page.user_label = Label(
            centered,
            text=settings["username"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        )
        Page.user_label.grid(column=1, row=1, sticky="w", pady=5)
        Label(
            centered,
            text=TEXTS["description"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=2, sticky="e", padx=50)
        Page.description_entry = Entry(
            centered,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        Page.description_entry.grid(column=1, row=2, sticky="w", pady=10)

        for u, d, n in client.account_list:
            if u == settings["username"]:
                Page.description_entry.insert(END, d)
                break

        Button(
            centered,
            text=TEXTS["save_description"],
            font=settings.font(13),
            fg=settings["color_text"],
            command=lambda: Page.description_action(Page.description_entry),
            bg=settings["color_bg_faded"],
            highlightbackground=settings["color_bg_faded"],
        ).grid(column=0, row=4, sticky="w", pady=10)
        Button(
            centered,
            text=TEXTS["log_out"],
            font=settings.font(13),
            fg=settings["color_text"],
            command=Page.log_out_action,
            bg=settings["color_bg_faded"],
            highlightbackground=settings["color_bg_faded"],
        ).grid(column=0, row=5, sticky="w")

        return root

    def log_out_action():
        client.send("log out")
        settings["username"] = ""
        settings["password"] = ""
        settings["logged_in"] = "0"
        Page.open("log in")
        window.update_user_list()

    def description_action(entry):
        description = entry.get()
        client.send("modify account", description)

    def settings():
        root = Frame(window.root, bg=settings["color_bg_main"])
        centered = Frame(root, bg=settings["color_bg_main"])
        centered.pack(padx=30, pady=40, anchor="w")

        Label(
            centered,
            text=TEXTS["settings"],
            font=settings.font(15),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=0, sticky="w", pady=20)

        Label(
            centered,
            text=TEXTS["design"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=1, sticky="ne", padx=50)
        styles = ("Light", "Dark", "Whatsapp")
        l = Listbox(
            centered,
            height=len(styles),
            relief="solid",
            highlightthickness=0,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        )
        l.grid(column=1, row=1, sticky="w")
        for style in styles:
            l.insert(END, style)
        l.select_set(0)

        Label(
            centered,
            text="Server IP",
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=2, sticky="e", padx=50)
        e1 = Entry(
            centered,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e1.grid(column=1, row=2, sticky="w", pady=10)
        e1.insert(END, settings["ip"])

        e3 = IntVar(value=int(settings["localhost"]))
        c = Checkbutton(
            centered,
            text=TEXTS["same_pc"],
            font=settings.font(13),
            fg=settings["color_text"],
            variable=e3,
            bg=settings["color_bg_main"],
        )
        c.grid(column=2, row=2, sticky="w", pady=10)

        Label(
            centered,
            text=TEXTS["server_port"],
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
        ).grid(column=0, row=3, sticky="e", padx=50)
        e2 = Entry(
            centered,
            font=settings.font(13),
            fg=settings["color_text"],
            bg=settings["color_bg_main"],
            highlightbackground=settings["color_text"],
            highlightthickness=1,
            bd=0,
            insertbackground=settings["color_text"],
            highlightcolor=settings["color_text"],
        )
        e2.grid(column=1, row=3, sticky="w", pady=10)
        e2.insert(END, settings["port"])

        b = Button(
            centered,
            text=TEXTS["save"],
            font=settings.font(13),
            fg=settings["color_text"],
            command=lambda: Page.settings_action(l, e1, e2, e3),
            bg=settings["color_bg_faded"],
            highlightbackground=settings["color_bg_faded"],
        ).grid(column=0, row=4, sticky="w", pady=10)
        return root

    def settings_action(l, e1, e2, e3):
        index = l.curselection()
        if not index:
            style = "custom"
        else:
            style = ("light", "dark", "whatsapp")[index[0]]
        settings.style(style)
        settings["ip"] = e1.get()
        settings["port"] = e2.get()
        settings["localhost"] = e3.get()
        if int(settings["localhost"]):
            settings["ip"] = socket.gethostname()
        if style != "custom":
            Page.info(TEXTS["design_restart_info"])

    def open(page):
        if page == Page.opened:
            return
        window.root.unbind("<Button-1>")
        if page == "profile" and settings["logged_in"] == "0":
            page = "log in"
        if Page.opened:
            Page.pages[Page.opened].place_forget()
        if page[0] == "%":
            if not page in Page.pages:
                Page.pages[page] = Chat(page)
            else:
                c = Page.pages[page]
                keys = list(c.message_widgets.keys())
                for i in keys:
                    for widget in c.message_widgets[i][0]:
                        c.canvas.delete(widget)
                c.messages = {}
                c.after(10, Page.pages[page].update)
            for i, (u, *_) in enumerate(client.account_list):
                if page[1:] == u:
                    client.account_list[i][2] = 0

        Page.opened = page
        window.update_user_list()
        Page.pages[page].place(
            x=window.user_width, y=0, relw=1, w=-window.user_width, relh=1
        )


class Chat(Frame):
    def __init__(self, chatname):
        super().__init__(bg=settings["color_bg_chat"])
        self.fonts = (
            tkfont.Font(font=settings.font(13)),
            tkfont.Font(font=settings.font(10)),
        )

        self.canvas = Canvas(self, bg=settings["color_bg_chat"], highlightthickness=0)
        self.canvas.place(x=0, y=0, relw=1, relh=1, h=-window.bar_height + 2)
        self.canvas.bind("<MouseWheel>", self.scroll_event)
        self.canvas.bind("<Configure>", self.resize_event)

        self.canvas.config(yscrollincrement=1)

        self.canvas_width = 0
        self.canvas_height = 0

        self.y = 0  # Message offset
        self.message_widgets = {}
        self.message_first = -2
        self.messages = {}

        self.input_bar = Canvas(
            self, bg=settings["color_bg_chat"], highlightthickness=0
        )
        self.input_bar.place(
            x=0, rely=1, y=-window.bar_height + 2, relw=1, h=window.bar_height - 2
        )

        self.input_bar.create_oval(
            2,
            2,
            window.bar_height - 4,
            window.bar_height - 4,
            fill=settings["color_bg_message"],
            outline="",
        )
        self.input_bar.create_oval(
            window.user_width * 2 - window.bar_height + 2,
            2,
            window.user_width * 2 - 2 * window.bar_height + 8,
            window.bar_height - 4,
            fill=settings["color_bg_message"],
            outline="",
            tags="replace",
        )

        self.input_bar.create_oval(
            window.user_width * 2 - window.bar_height + 4,
            2,
            window.user_width * 2 - 2,
            window.bar_height - 4,
            fill=settings["color_secondary_button"],
            outline="",
            tags="send",
        )
        self.input_bar.create_text(
            (
                window.user_width * 2 - window.bar_height // 2 + 1,
                (window.bar_height - 4) // 2,
            ),
            text="\u27A2",
            font=settings.font(16),
            fill=settings["color_text_inversed"],
            tags="send",
        )

        self.input_bar.tag_bind("send", "<Button-1>", self.send)
        self.message_input = Entry(
            self,
            highlightthickness=0,
            bd=0,
            font=self.fonts[0],
            relief="flat",
            bg=settings["color_bg_message"],
            fg=settings["color_text"],
            insertbackground=settings["color_text"],
        )
        self.message_input.place(
            x=(window.bar_height - 2) // 2,
            rely=1.0,
            y=-window.bar_height + 4,
            relw=1,
            w=-(window.bar_height - 2) * 2,
            h=window.bar_height - 6,
        )
        self.message_input.bind("<Enter>", lambda _: window.root.unbind("<Button-1>"))
        self.message_input.bind(
            "<Leave>",
            lambda _: window.root.bind("<Button-1>", lambda _: window.root.focus()),
        )
        self.message_input.bind("<Return>", lambda _: self.send())

    def send(self, *args):
        content = self.message_input.get()
        if content:
            window.root.focus()
            window._send(content)
            self.message_input.delete(0, END)

    def scroll_event(self, event):
        self.y = max(0, self.y + event.delta)
        self.canvas.yview_scroll(-event.delta, "units")
        self.update()

    def resize_event(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height

        widgets = list(self.message_widgets.keys())
        for i in widgets:
            for widget in self.message_widgets[i][0]:
                self.canvas.delete(widget)
            del self.message_widgets[i]

        self.update()

        self.input_bar.delete("send")
        self.input_bar.delete("replace")
        self.input_bar.create_oval(
            self.canvas_width - window.bar_height + 2,
            2,
            self.canvas_width - 2 * window.bar_height + 8,
            window.bar_height - 4,
            fill=settings["color_bg_message"],
            outline="",
            tags="replace",
        )
        self.input_bar.create_oval(
            self.canvas_width - window.bar_height + 4,
            2,
            self.canvas_width - 2,
            window.bar_height - 4,
            fill=settings["color_secondary_button"],
            outline="",
            tags="send",
        )
        self.input_bar.create_text(
            (
                self.canvas_width - window.bar_height // 2 + 1,
                (window.bar_height - 4) // 2,
            ),
            text="\u27A2",
            font=settings.font(16),
            fill=settings["color_text_inversed"],
            tags="send",
        )

    def update(self):
        try:
            self.canvas.winfo_exists()
        except:
            return

        max_y = self.canvas_height
        message_y = 0

        visible_messages = []
        remaining = 2

        visible = ""
        for i, (time, sender, content) in sorted(
            self.messages.items(), reverse=True, key=lambda x: int(x[0])
        ):
            if self.message_widgets.get(i, None) is None:
                h, canvas_message = self.draw_message(
                    max_y - message_y, i, time, sender, content
                )
                self.message_widgets[i] = (canvas_message, h)

            else:
                h = self.message_widgets[i][1]
            message_y += h

            visible_messages.append(i)
            if message_y - self.y > max_y:
                remaining -= 1
            visible += self.messages[i][0]

            if not remaining:
                break
        else:
            if self.retrieve_message("before"):
                self.after(10, self.update)

        keys = list(self.message_widgets.keys())
        for i in keys:
            if not i in visible_messages:
                for widget in self.message_widgets[i][0]:
                    self.canvas.delete(widget)
                self.message_widgets.pop(i)

        bbox = self.canvas.bbox("all")
        if bbox is None:
            bbox = [0, 0, 0, 0]
        else:
            bbox = list(bbox)
        bbox[1] -= 2
        self.canvas.configure(scrollregion=bbox)
        self.canvas.update_idletasks()

    def retrieve_message(self, direction):
        if direction == "before":
            if self.messages:
                message_id = min(list(self.messages.keys()), key=lambda x: int(x))
            else:
                message_id = -1
        else:
            if self.messages:
                message_id = max(list(self.messages.keys()), key=lambda x: int(x))
            else:
                message_id = -1
        answer = client.send(
            "retrieve message",
            Page.opened[1:] + "%" + direction + "%" + str(message_id),
        ).split("%")

        if len(answer) != 4:
            return 0
        message_id, time, sender, content = answer

        self.messages[message_id] = (time, sender, content)
        if direction == "after":
            keys = list(self.message_widgets.keys())
            for i in keys:
                for widget in self.message_widgets[i][0]:
                    self.canvas.delete(widget)
            self.message_widgets = {}

        return 1

    def draw_message(self, y, message_id, time, sender, text):
        MARGIN = 5
        DIFFERENCE = MARGIN * 8
        INDENTATION = MARGIN * 3
        MIN_WIDTH = MARGIN * 10
        MAX_WIDTH = max(MIN_WIDTH, self.canvas_width - DIFFERENCE - INDENTATION)

        sender_colors = (
            "#2ced28",
            "#eddd28",
            "#d96f23",
            "#f2583d",
            "#f23da4",
            "#3df2d7",
            "#5c75f2",
            "#1ba7f2",
            "#c4f21b",
        )
        sender_color = sender_colors[sum([ord(i) for i in sender]) % len(sender_colors)]

        w = max(
            min(self.fonts[0].measure(text), MAX_WIDTH),
            self.fonts[1].measure(sender),
            self.fonts[1].measure(time),
            MIN_WIDTH,
        )
        if settings["username"] == sender:
            x = max(DIFFERENCE, self.canvas_width - INDENTATION - w)
        else:
            x = INDENTATION

        lines = ""
        words = text.split()
        line_length = 0
        line = ""
        for word in words:
            word_width = self.fonts[0].measure(word + " ")
            if line_length == 0 and word_width > w:
                for char in word:
                    char_width = self.fonts[0].measure(char)
                    if line_length + char_width > w:
                        lines += line + "\n"
                        line_length = 0
                        line = ""
                    line_length += char_width
                    line += char
                line += " "
            elif line_length + word_width > w:
                lines += line + "\n"
                line_length = 0
                line = ""
            line_length += word_width
            line += word + " "
        lines += line
        h = self.fonts[0].metrics("linespace") * (lines.count("\n") + 1)
        header_height = self.fonts[1].metrics("linespace")
        h += header_height * 2
        y -= h + 2 * MARGIN

        r = 25
        x1 = x - MARGIN
        x2 = x + MARGIN + w
        y1 = y - MARGIN
        y2 = y + MARGIN + h
        if settings["username"] == sender:
            sender = SENDER_SELF_NAME
            points = (
                x2 - r,
                y1,
                x2,
                y1,
                x2,
                y1 + r,
                x2,
                y2 - r,
                x2,
                y2,
                x2 - r,
                y2,
                x1 + r,
                y2,
                x1,
                y2,
                x1,
                y2 - r,
                x1,
                y1 + r,
                x1,
                y1,
                x1 + r,
                y1,
            )
            p1 = self.canvas.create_polygon(
                points, tag="m", fill=settings["color_bg_own_message"], smooth=True
            )
            p2 = self.canvas.create_polygon(
                (x2 - 8, y1, x2 + 10, y1, x2, y1 + 8),
                tag="m",
                fill=settings["color_bg_own_message"],
            )
        else:
            points = (
                x2 - r,
                y1,
                x2,
                y1,
                x2,
                y1 + r,
                x2,
                y2 - r,
                x2,
                y2,
                x2 - r,
                y2,
                x1 + r,
                y2,
                x1,
                y2,
                x1,
                y2 - r,
                x1,
                y1 + r,
                x1,
                y1,
                x1 + r,
                y1,
            )
            p1 = self.canvas.create_polygon(
                points, tag="m", fill=settings["color_bg_message"], smooth=True
            )
            p2 = self.canvas.create_polygon(
                (x1 - 8, y1, x1 + 10, y1, x1, y1 + 8),
                tag="m",
                fill=settings["color_bg_message"],
            )
        t1 = self.canvas.create_text(
            (x, y - 1),
            tag="m",
            font=self.fonts[1],
            text=sender,
            anchor="nw",
            fill=sender_color,
        )
        t2 = self.canvas.create_text(
            (x, y + header_height),
            tag="m",
            font=self.fonts[0],
            text=text,
            w=w,
            anchor="nw",
            fill=settings["color_text"],
        )
        t3 = self.canvas.create_text(
            (x + w, y + h - header_height + 1),
            tag="m",
            font=self.fonts[1],
            text=time,
            anchor="ne",
            fill=settings["color_text_faded"],
        )

        return h + 3 * MARGIN, (p1, p2, t1, t2, t3)


class Settings(dict):
    def __init__(self, path):
        super().__init__()
        self.load(path)

    def load(self, path):
        try:
            with open(path, "r") as file:
                content = file.readlines()
        except FileNotFoundError:
            content = ()

        loaded = {}
        for line in content:
            key, value = line.replace(" ", "").split(":")
            loaded[key] = value.replace("\n", "")

        for line in self.default():
            key, value = line.replace(" ", "").split(":")
            self[key] = loaded.get(key, value)

        self["logged_in"] = "0"

    def log_in(self):
        if int(self["stay_logged_in"]) and not (
            self["username"] is None or self["password"] is None
        ):
            Page.log_in_action(self["username"], self["password"], direct=1)

    def save(self, path):
        if not int(self["stay_logged_in"]):
            self["username"] = "None"
            self["password"] = "None"

        if int(self["localhost"]):
            self["ip"] = "None"

        content = (
            str(settings)[1:-2].replace(", ", "\n").replace("'", "").replace('"', "")
        )

        with open(path, "w") as file:
            file.write(content)

    def default(self):
        return (
            "username:",
            "password:",
            "ip:",
            "port: 50007",
            "localhost: 1",
            "stay_logged_in: 0",
            "logged_in: 0",
            "font_type: TkDefaultFont",
            "font_size: 1.0",
            "color_text: #000000",
            "color_text_link: #8ab5f8",
            "color_text_inversed: #fffffe",
            "color_text_faded: #888888",
            "color_main_button: #fffffe",
            "color_secondary_button: #008b78",
            "color_bg_chat: #eee6dd",
            "color_bg_main: #fffffe",
            "color_bg_faded: #f8f8f8",
            "color_bg_message: #fffffe",
            "color_bg_own_message: #dcf8c6",
            "color_bg_bar: #eeeeee",
            "color_bg_user: #fffffe",
        )

    def style(self, name):
        light = (
            "font_type: TkDefaultFont",
            "font_size: 1.0",
            "color_text: #000000",
            "color_text_link: #8ab5f8",
            "color_text_inversed: #000000",
            "color_text_faded: #888888",
            "color_main_button: #fffffe",
            "color_secondary_button: #fffffe",
            "color_bg_chat: #dddddd",
            "color_bg_main: #fffffe",
            "color_bg_faded: #f8f8f8",
            "color_bg_message: #fffffe",
            "color_bg_own_message: #efefef",
            "color_bg_bar: #eeeeee",
            "color_bg_user: #fffffe",
        )

        dark = (
            "font_type: TkDefaultFont",
            "font_size: 1.0",
            "color_text: #fffffe",
            "color_text_link: #8ab5f8",
            "color_text_inversed: #eeeeee",
            "color_text_faded: #888888",
            "color_main_button: #606060",
            "color_secondary_button: #444444",
            "color_bg_chat: #101010",
            "color_bg_main: #020202",
            "color_bg_faded: #202020",
            "color_bg_message: #404040",
            "color_bg_own_message: #303030",
            "color_bg_bar: #404040",
            "color_bg_user: #000000",
        )

        whatsapp = (
            "font_type: TkDefaultFont",
            "font_size: 1.0",
            "color_text: #000000",
            "color_text_link: #8ab5f8",
            "color_text_inversed: #fffffe",
            "color_text_faded: #888888",
            "color_main_button: #fffffe",
            "color_secondary_button: #008b78",
            "color_bg_chat: #eee6dd",
            "color_bg_main: #fffffe",
            "color_bg_faded: #f8f8f8",
            "color_bg_message: #fffffe",
            "color_bg_own_message: #dcf8c6",
            "color_bg_bar: #eeeeee",
            "color_bg_user: #fffffe",
        )

        for i in range(len(light)):
            key = 0
            if name == "light":
                key, value = light[i].replace(" ", "").split(":")
            elif name == "dark":
                key, value = dark[i].replace(" ", "").split(":")
            elif name == "whatsapp":
                key, value = whatsapp[i].replace(" ", "").split(":")
            if key:
                self[key] = value

    def font(self, size):
        return self["font_type"], int(float(self["font_size"]) * size)


def get_config():
    if "--config" in sys.argv:
        index = sys.argv.index("--config") + 1
        if index < len(sys.argv):
            cwd = os.getcwd()
            return os.path.join(cwd, sys.argv[index])

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(script_dir, os.path.pardir, "data", "client.config")


if __name__ == "__main__":
    config_file = get_config()
    settings = Settings(config_file)
    window = Window("Messenger")
    client = Client()
    Page()
    Page.open("log in")
    settings.log_in()
    window.start()
    settings.save(config_file)
