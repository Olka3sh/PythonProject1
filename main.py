import tkinter as tk
from tkinter import scrolledtext
import os
import platform
import getpass
import shlex
import re
import sys
import zipfile


class ShellEmulator(tk.Tk):
    def __init__(self):
        super().__init__()

        # ЭТАП 2. Парсинг аргументов
        self.vfs_path = None
        self.startup_script = None
        args = sys.argv[1:]
        i = 0
        while i < len(args):
            if args[i] == '--vfs-path' and i + 1 < len(args):
                self.vfs_path = args[i + 1]
                i += 1
            elif args[i] == '--startup-script' and i + 1 < len(args):
                self.startup_script = args[i + 1]
                i += 1
            i += 1

        # ЭТАП 3: Структуры VFS
        self.files = {}
        self.dirs = set()
        self.current_dir = "/"

        # ЭТАП 3: Загрузка VFS
        if self.vfs_path:
            self.load_vfs(self.vfs_path)   # Загрузка из ZIP архива
        else:
            self.create_default_vfs()      # Создание VFS по умолчанию

        # ЭТАП 1: Настройка переменных окружения
        if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:
            os.environ['HOME'] = os.environ['USERPROFILE']

        # ЭТАП 1: Инициализация REPL
        self.history = []
        self.history_index = -1
        self.setup_ui()                  # Настройка графического интерфейса
        self.display_welcome()           # Приветственное сообщение

        # ЭТАП 2: Запуск стартового скрипта
        if self.startup_script:
            self.after(100, self.run_startup_script)

    def expand_variables(self, text):
        # Этап 3: Раскрытие переменных окружения в формате $VAR

        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)

    def load_vfs(self, zip_path):
        # Этап 3: Загрузка VFS из ZIP архива
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    path = file_info.filename
                    if not file_info.is_dir():
                        with zip_ref.open(path) as file:
                            content = file.read().decode('utf-8')
                            self.files[path] = content

                        # Добавляем родительскую директорию
                        dir_path = os.path.dirname(path)
                        if dir_path:
                            self.dirs.add(dir_path)

                # Корневая директория
                self.dirs.add("")
        # ЭТАП 3: Сообщение об ошибке загрузки VFS
        except Exception as e:
            self.display_output(f"Error loading VFS: {e}")
            self.create_default_vfs()

    def create_default_vfs(self):
        # Этап 3: Создание VFS по умолчанию в памяти
        self.files = {
            "readme.txt": "Default VFS for variant 26",
            "bin/hello.sh": "echo 'Hello World'",
            "docs/help.txt": "Available commands: ls, cd, history, du, exit",
            "home/user/documents/file1.txt": "Document 1 content",
            "home/user/documents/file2.txt": "Document 2 content",
            "var/log/system.log": "Log line 1\nLog line 2\nLog line 3"
        }
        # ЭТАП 3: Структура с 3+ уровнями вложенности
        self.dirs = {"", "bin", "docs", "home", "home/user", "home/user/documents", "var", "var/log"}

    def list_dir(self, path):
        # ЭТАП 4: Список содержимого директории
        if path == ".":
            path = self.current_dir
        elif path == "..":
            path = self.get_parent_dir(self.current_dir)

        files = []
        dirs = []

        # Поиск файлов в указанной директории
        for file_path in self.files.keys():
            dir_name = os.path.dirname(file_path) or ""
            if dir_name == path:
                files.append(os.path.basename(file_path))

        # Поиск поддиректорий
        for dir_path in self.dirs:
            if dir_path != path:
                parent = os.path.dirname(dir_path) or ""
                if parent == path and dir_path:
                    dirs.append(os.path.basename(dir_path))

        return sorted(dirs), sorted(files)

    def get_parent_dir(self, path):
        # ЭТАП 4: Получение родительской директории
        if path == "/":
            return "/"
        parent = os.path.dirname(path)
        return parent if parent else "/"

    # ЭТАП 1: Настройка графического интерфейса
    def setup_ui(self):
        username = getpass.getuser()
        hostname = platform.node()
        self.title(f"Эмулятор - [{username}@{hostname}]")
        self.geometry("800x600")
        # Область вывода
        self.output_area = scrolledtext.ScrolledText(
            self, state='disabled', wrap='word',
            bg='black', fg='white', font=('Consolas', 12)
        )
        self.output_area.pack(expand=True, fill='both')
        # Фрейм ввода команды
        input_frame = tk.Frame(self, bg='black')
        input_frame.pack(fill='x')

        tk.Label(input_frame, text=">", fg='white', bg='black').pack(side='left')
        self.input_entry = tk.Entry(input_frame, bg='black', fg='white')
        self.input_entry.pack(side='left', expand=True, fill='x')
        self.input_entry.focus_set()
        self.input_entry.bind("<Return>", self.on_enter)

    def display_welcome(self):
        # ЭТАП 1: Приветственное сообщение
        self.display_output("Shell Emulator - Variant 26")
        self.display_output(f"VFS: {self.vfs_path or 'default'}")
        self.display_output("Commands: ls, cd, history, du, exit")
        self.display_output("-" * 50)

    def display_output(self, text):
        #ЭТАП 1: Вывод текста в интерфейс
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.config(state='disabled')
        self.output_area.see(tk.END)

    def on_enter(self, event=None):
        # ЭТАП 1: Обработка ввода команды
        command = self.input_entry.get().strip()
        if not command:
            return

        # Сохранение в истории
        self.history.append(command)
        self.history_index = len(self.history)
        self.display_output(f"> {command}")
        self.execute_command(command)
        self.input_entry.delete(0, tk.END)

    def execute_command(self, command_line):
        # Раскрытие переменных окружения
        command_line = self.expand_variables(command_line)
        parts = shlex.split(command_line)
        if not parts:
            return

        command = parts[0]
        args = parts[1:]

        if command == "ls":
            self.command_ls(args)
        elif command == "cd":
            self.command_cd(args)
        elif command == "history":
            self.command_history(args)
        elif command == "du":
            self.command_du(args)
        elif command == "exit":
            self.quit()
        else:
            self.display_output(f"Command not found: {command}")

    def command_ls(self, args):
        path = args[0] if args else "."
        try:
            dirs, files = self.list_dir(path)
            self.display_output(f"Directory: {path}")
            for d in dirs:
                self.display_output(f"  {d}/")
            for f in files:
                self.display_output(f"  {f}")
            if not dirs and not files:
                self.display_output("  (empty)")
        except:
            self.display_output(f"ls: {path}: No such directory")

    def command_cd(self, args):
        if not args:
            self.current_dir = "/"
        else:
            path = args[0]
            if path == "/":
                self.current_dir = "/"
            elif path == "..":
                self.current_dir = self.get_parent_dir(self.current_dir)
            else:
                # Простая проверка существования директории
                new_dir_exists = False
                for dir_path in self.dirs:
                    if dir_path == path:
                        new_dir_exists = True
                        break
                if new_dir_exists:
                    self.current_dir = path
                else:
                    self.display_output(f"cd: {path}: No such directory")
                    return

        self.display_output(f"Current directory: {self.current_dir}")

    def command_history(self, args):
        for i, cmd in enumerate(self.history, 1):
            self.display_output(f"{i}  {cmd}")

    def command_du(self, args):
        path = args[0] if args else self.current_dir
        total_size = 0

        # Подсчет размера файлов в текущей директории
        for file_path, content in self.files.items():
            file_dir = os.path.dirname(file_path) or ""
            if file_dir == path:
                file_size = len(content)
                total_size += file_size
                self.display_output(f"{file_size:8}  {os.path.basename(file_path)}")

        self.display_output(f"{total_size:8}  .")

    # ЭТАП 2: Выполнение стартового скрипта
    def run_startup_script(self):
        try:
            with open(self.startup_script, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.display_output(f"> {line}")
                        self.execute_command(line)
        except Exception as e:
            self.display_output(f"Script error: {e}")


if __name__ == "__main__":
    app = ShellEmulator()
    app.mainloop()