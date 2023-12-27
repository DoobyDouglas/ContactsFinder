# pyinstaller --noconfirm --noconsole --onefile --add-data 'bg.png;.' --add-data 'ico.ico;.' --icon=ico.ico ContactsFinder.py
from asyncio import run
import re
import sys
import ttkbootstrap as tb
import os
import tkinter
from threading import Thread
from PIL import Image, ImageTk
import tkinter.messagebox
import ctypes
from tkinter import TclError
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from aiohttp.client_exceptions import InvalidURL
from errors import INVALID_URL, UNDEFINED


class ContactsFinder:

    NAME = 'ContactsFinder'
    VERSION = 0.01
    PARSER = BeautifulSoup
    CLIENT = ClientSession
    email_regex = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'
    phone_regex = r'\+[7]\s?[\d\s\-]+'

    def __init__(self) -> None:
        self.master = tb.Window(themename='pulse')
        self.master.title(f'{self.NAME} v{self.VERSION:.2f}')
        self.master.geometry(self.__set_geometry())
        self.master.resizable(False, False)
        self.master.iconbitmap(default=self.__resource_path('ico.ico'))
        self.master.iconbitmap(self.__resource_path('ico.ico'))
        self.master.protocol('WM_DELETE_WINDOW', self.__on_close)
        self.raw_img = ImageTk.PhotoImage(
            Image.open(self.__resource_path('bg.png'))
        )
        self.background_label = tkinter.Label(
            self.master,
            name='background_pic',
            image=self.raw_img,
        )
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.style = tb.Style()
        self.style.configure('Horizontal.TProgressbar', thickness=27)
        self.__create_widgets()

    def __create_widgets(self) -> None:
        self.url_label = tb.Label(
            self.master,
            name='url_entry_label',
            text='Введите URL:'
        )
        self.url_label.grid(sticky='w', padx=10, pady=10)
        self.url_entry = tb.Entry(
            self.master,
            bootstyle='info',
            name='url_entry',
            width=40,
        )
        self.url_entry.grid(sticky='w', padx=10, pady=10)
        self.url_entry.bind('<Key>', self.__if_rus_keys_entry)
        self.get_bttn = tb.Button(
            self.master,
            bootstyle='info',
            text='Получить контакты',
            name='get_contacts',
            width=20,
            command=lambda: self.__get_contacts_thread(
                f'{self.url_entry.get().strip()}'
            ),
        )
        self.get_bttn.grid(sticky='w', padx=120, pady=10)
        self.text_frame = tb.Frame(self.master)
        self.text_frame.grid(sticky='w')
        self.text = tb.Text(self.text_frame, width=40, height=8)
        self.text.grid(row=0, column=0, sticky='w', padx=10, pady=10)
        self.text.config(state=tb.DISABLED)
        self.text.bind('<Key>', self.__if_rus_keys_text)
        scrollbar = tb.Scrollbar(
            self.text_frame,
            orient='vertical',
            bootstyle='info',
            command=self.text.yview,
        )
        scrollbar.grid(row=0, column=1, sticky='ns', pady=9)
        self.text.config(yscrollcommand=scrollbar.set)

        self.progressbar = tb.Progressbar(
            self.master,
            mode='determinate',
            name='pb',
            length=100,
            style='Horizontal.TProgressbar',
            bootstyle='warning',
        )

        self.progressbar.place(relx=0.5, rely=1.0, anchor='ne', y=-194, x=-140)

    async def __get_contacts(self, url: str) -> None:
        emails = set()
        phones = set()
        self.text.config(state=tb.NORMAL)
        self.text.delete('1.0', tb.END)
        self.text.config(state=tb.DISABLED)
        try:
            async with self.CLIENT() as session:
                async with session.get(url) as response:
                    parser = self.PARSER(await response.text(), 'lxml')
                    email_pattern = re.compile(self.email_regex)
                    phone_pattern = re.compile(self.phone_regex)
                    self.progressbar.config(maximum=(len(parser.findAll())))
                    for i in parser.findAll():
                        email_matches = email_pattern.findall(str(i))
                        phone_matches = phone_pattern.findall(str(i))
                        phone_matches = [
                            i.replace('-', '').replace(' ', '')
                            for i in phone_matches
                        ]
                        for match in email_matches:
                            emails.add(match)
                        for match in phone_matches:
                            if 11 <= len(match) <= 12:
                                phones.add(match)
                        self.progressbar.step(1)

        except InvalidURL:
            self.text.config(state=tb.NORMAL)
            self.text.delete('1.0', tb.END)
            self.text.insert(tb.END, INVALID_URL)
            self.text.config(state=tb.DISABLED)
        except Exception:
            self.text.config(state=tb.NORMAL)
            self.text.delete('1.0', tb.END)
            self.text.insert(tb.END, UNDEFINED)
            self.text.config(state=tb.DISABLED)
        self.text.config(state=tb.NORMAL)
        for i in emails:
            self.text.insert(tb.END, f'{i}\n')
        for i in phones:
            self.text.insert(tb.END, f'{i}\n')
        self.text.config(state=tb.DISABLED)
        self.progressbar['value'] = 0

    def __get_contacts_thread(self, url: str) -> None:
        Thread(target=self.__run_get_contacts_thread, args=(url,)).start()

    def __run_get_contacts_thread(self, url: str) -> None:
        run(self.__get_contacts(url))

    def __resource_path(self, path: str) -> str:
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath('.')
        return os.path.join(base_path, path)

    def __if_rus_keys_entry(self, event: tkinter.Event) -> None:
        keyboard = getattr(
            ctypes.windll.LoadLibrary('user32.dll'),
            'GetKeyboardLayout'
        )
        if hex(keyboard(0)) != '0x4190419':
            return
        try:
            if event.state == 4:
                if event.keycode == 86:
                    if self.url_entry.selection_present():
                        self.url_entry.delete(
                            tb.SEL_FIRST, tb.SEL_LAST
                        )
                        self.url_entry.insert(
                            tb.INSERT, self.master.clipboard_get()
                        )
                    else:
                        self.url_entry.insert(
                            self.url_entry.index(tb.INSERT),
                            self.master.clipboard_get()
                        )
                elif event.keycode == 65:
                    self.url_entry.selection_range(0, tb.END)
                elif event.keycode == 67:
                    if self.url_entry.selection_present():
                        self.master.clipboard_clear()
                        self.master.clipboard_append(
                            self.url_entry.selection_get()
                        )
                        self.master.update()
                elif event.keycode == 88:
                    if self.url_entry.selection_present():
                        self.master.clipboard_clear()
                        self.master.clipboard_append(
                            self.url_entry.selection_get()
                        )
                        self.url_entry.delete(
                            tb.SEL_FIRST, tb.SEL_LAST
                        )
                        self.master.update()
        except TclError:
            pass
        except Exception:
            self.text.config(state=tb.NORMAL)
            self.text.delete('1.0', tb.END)
            self.text.insert(tb.END, UNDEFINED)
            self.text.config(state=tb.DISABLED)

    def __if_rus_keys_text(self, event: tkinter.Event) -> None:
        keyboard = getattr(
            ctypes.windll.LoadLibrary('user32.dll'),
            'GetKeyboardLayout'
        )
        if hex(keyboard(0)) != '0x4190419':
            return
        try:
            if event.state == 4:
                if event.keycode == 86:
                    if bool(self.text.tag_ranges(tb.SEL)):
                        self.text.delete(tb.SEL_FIRST, tb.SEL_LAST)
                        self.text.insert(
                            tb.INSERT, self.master.clipboard_get()
                        )
                    else:
                        self.text.insert(
                            self.text.index(tb.INSERT),
                            self.master.clipboard_get()
                        )
                elif event.keycode == 65:
                    self.text.tag_add(tb.SEL, '1.0', tb.END)
                elif event.keycode == 67:
                    if bool(self.text.tag_ranges(tb.SEL)):
                        self.master.clipboard_clear()
                        self.master.clipboard_append(self.text.selection_get())
                        self.master.update()
                elif event.keycode == 88:
                    if bool(self.text.tag_ranges(tb.SEL)):
                        self.master.clipboard_clear()
                        self.master.clipboard_append(self.text.selection_get())
                        self.text.delete(tb.SEL_FIRST, tb.SEL_LAST)
                        self.master.update()
        except TclError:
            pass
        except Exception:
            self.text.config(state=tb.NORMAL)
            self.text.delete('1.0', tb.END)
            self.text.insert(tb.END, UNDEFINED)
            self.text.config(state=tb.DISABLED)

    def __set_geometry(self) -> str:
        width = 500
        height = 292
        to_right = self.master.winfo_screenwidth() // 8
        x = (self.master.winfo_screenwidth() - width) // 2
        y = (self.master.winfo_screenheight() - height) // 3
        return f'{width}x{height}+{x + to_right}+{y}'

    def __on_close(self):
        os._exit(1)


if __name__ == '__main__':
    contactsFinder = ContactsFinder()
    contactsFinder.master.focus_force()
    contactsFinder.master.mainloop()
