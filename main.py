import tkinter as tk
from tkinter import scrolledtext
import os
import platform
import getpass
import shlex
import re


class ShellEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:    # Настройка переменных окружения
            os.environ['HOME'] = os.environ['USERPROFILE']

        self.history = []
        self.history_index = -1
        self._setup_ui()
        self._display_welcome()
        self._display_prompt()

    # 1.1: Приложение в форме GUI
    def _setup_ui(self):
        self.title(self._get_window_title())
        self.geometry("800x600")
        self.output_area = scrolledtext.ScrolledText(                    # Output area
            self, state='disabled', wrap='word',
            bg='black', fg='white', font=('Consolas', 12)
        )
        self.output_area.pack(expand=True, fill='both', padx=0, pady=0)
        input_frame = tk.Frame(self, bg='black')                        # Input area
        input_frame.pack(fill='x', padx=0, pady=0)

        tk.Label(input_frame, text=">", fg='white', bg='black', font=('Consolas', 12)).pack(side='left')

        self.input_entry = tk.Entry(
            input_frame, bg='black', fg='white',
            insertbackground='white', font=('Consolas', 12)
        )
        self.input_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))
        self.input_entry.focus_set()
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.bind("<Up>", self._history_up)
        self.input_entry.bind("<Down>", self._history_down)

    # 1.2: Формирование заголовка на основе реальных данных ОС
    def _get_window_title(self):
        username = getpass.getuser()
        hostname = platform.node()
        return f"Эмулятор - [{username}@{hostname}]"

    def _display_welcome(self):
        self._display_output("Welcome to the Shell Emulator!")
        self._display_output("Available commands: ls, cd, exit")
        self._display_output("Environment variable expansion supported: $HOME, $USER, etc.")
        self._display_output("-" * 50)

    def _display_output(self, text):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.config(state='disabled')
        self.output_area.see(tk.END)

    def _display_prompt(self):
        self.input_entry.delete(0, tk.END)
        self.output_area.config(state='normal')
        self.output_area.config(state='disabled')
        self.output_area.see(tk.END)

    def _on_enter(self, event=None):
        command = self.input_entry.get().strip()
        if not command:
            return

        self.history.append(command)
        self.history_index = len(self.history)

        self._display_output(f"> {command}")
        self._execute_command(command)
        self._display_prompt()

    def _history_up(self, event=None):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.history[self.history_index])
        return "break"

    def _history_down(self, event=None):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.history[self.history_index])
        return "break"

    # 1.3: Парсер с поддержкой раскрытия переменных окружения
    def _split_and_expand(self, command_line: str):
        try:
            tokens = shlex.split(command_line, posix=True)
        except ValueError as e:
            self._display_output(f"parse error: {e}")
            return []

        def expand_env_all(s: str) -> str:
            s1 = os.path.expanduser(s)

            def repl(m):
                name = m.group(1) or m.group(2)
                return os.environ.get(name, m.group(0))

            s2 = re.sub(r"\$(\w+)|\$\{([^}]+)\}", repl, s1)
            s3 = os.path.expandvars(s2)
            return s3

        return [expand_env_all(t) for t in tokens]

    def _execute_command(self, command_line):
        parts = self._split_and_expand(command_line)
        if not parts:
            return
        command, args = parts[0], parts[1:]

        if command == "ls":
            self._command_ls(args)
        elif command == "cd":
            self._command_cd(args)
        elif command == "exit":
            self.quit()
        else:                                                   # 1.6: Обработка ошибок - неизвестная команда
            raw = command_line.strip()
            if len(parts) == 1:
                if raw.startswith('~') or raw.startswith('$'):
                    self._display_output(parts[0])
                    return
            self._display_output(f"Command not found: {command}")

    def _command_ls(self, args):                              # 1.4: Команда-заглушка ls - выводит имя и аргументы
        self._display_output(f"ls called with arguments: {args}")
        self._display_output("file1.txt  file2.txt  directory/")
        self._display_output("(this is a stub implementation)")

    def _command_cd(self, args):                              # 1.4: Команда-заглушка cd - выводит имя и аргументы
        self._display_output(f"cd called with arguments: {args}")
        if args:
            self._display_output(f"Would change to directory: {args[0]}")
        else:
            self._display_output("Would change to home directory")
        self._display_output("(this is a stub implementation)")


if __name__ == "__main__":
    app = ShellEmulator()
    app.mainloop()