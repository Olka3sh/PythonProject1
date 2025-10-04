import tkinter as tk
from tkinter import scrolledtext
import os
import platform
import getpass
import shlex
import re
import sys
import zipfile
import base64

class ShellEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.history = []                   # Инициализация списка истории команд
        self.history_index = -1             # Индекс для навигации по истории
        self.current_dir = "/"              # Свойство для хранения текущей рабочей директории
        self.setup_ui()                     # Настройка графического интерфейса

        self.vfs_path = None
        self.startup_script = None
        args = sys.argv[1:]                 # Список аргументов командной строки
        i = 0
        while i < len(args):
            if args[i] == '-vfs' and i + 1 < len(args):       # Проверка на путь к физ расположению VFS
                self.vfs_path = args[i + 1]                   # Сохранение пути к VFS
                i += 1
            elif args[i] == '-script' and i + 1 < len(args):  # Проверка на путь к стартовому скрипту
                self.startup_script = args[i + 1]             # Сохранение пути к начальному скрипту
                i += 1
            i += 1

        self.files = {}                   # Файлы хранятся в памяти
        self.dirs = set()                 # Директории хранятся в памяти
        self.file_permissions = {}        # ЭТАП 5: Права доступа для файлов

        if self.vfs_path:
            self.load_vfs(self.vfs_path)  # Загрузка из ZIP архива

        self.display_welcome()

        if self.startup_script:
            self.after(100, self.run_startup_script)

    def _split_and_expand(self, command_line: str):        # Парсинг и раскрытие переменных
        try:
            tokens = shlex.split(command_line, posix=True) # Разделение строки на части по " ", /
        except ValueError as e: # Есть ошибка
            self.display_output(f"parse error: {e}")
            return []

        def expand_env_all(s: str) -> str:                 # Функция раскрытия переменных
            s1 = os.path.expanduser(s)                     # Заменяет символ ~ на полный путь к домашней директории

            def repl(m):                                   # 2. Раскрытие $VAR и ${VAR}
                name = m.group(1) or m.group(2)
                if os.name == 'nt':
                    if name.upper() == 'HOME' and name not in os.environ:
                        return os.environ.get('USERPROFILE', m.group(0))
                return os.environ.get(name, m.group(0))   # Ищет переменную в окружении, если не находит - возвращает исходный текст

            s2 = re.sub(r"\$(\w+)|\$\{([^}]+)\}", repl, s1) # Регулярное выражение
            s3 = os.path.expandvars(s2)                   # Дополнительное раскрытие (резервный механизм)
            return s3
        return [expand_env_all(t) for t in tokens] # Возвращает список полностью обработанных токенов

    # ЭТАП 1: Настройка графического интерфейса
    def setup_ui(self):
        username = getpass.getuser()                       # Получение имени текущего пользователя ОС
        hostname = platform.node()                         # Получение сетевого имени компьютера
        self.title(f"Эмулятор - [{username}@{hostname}]")  # Установка заголовка окна
        self.geometry("800x600")                           # Установка размера окна
        self.output_area = scrolledtext.ScrolledText(      # Область вывода с возможностью скролла
            self, state='disabled', wrap='word',
            bg='black', fg='white', font=('Consolas', 12)
        )
        self.output_area.pack(expand=True, fill='both')    # Размещение текстового поля в окне
        input_frame = tk.Frame(self, bg='black')           # Создание фрейма ввода команды
        input_frame.pack(fill='x')                         # Размещение фрейма в окне
        tk.Label(input_frame, text=">", fg='white', bg='black').pack(side='left')  # Создание текстовой метки ">"
        self.input_entry = tk.Entry(input_frame, bg='black', fg='white')           # Создание однострочного поля для ввода
        self.input_entry.pack(side='left', expand=True, fill='x')                  # Размещение поля в окне
        self.input_entry.focus_set()                      # Установка курсора на поле ввода
        self.input_entry.bind("<Return>", self.on_enter)  # Привязывание обработчика нажатия enter

    def display_welcome(self):
        self.display_output("Shell Emulator - Variant 26")
        self.display_output(f"VFS: {self.vfs_path or 'default'}")
        self.display_output("Commands: ls, cd, history, du, rm, chmod, exit")
        self.display_output("-" * 50)

    def display_output(self, text):
        self.output_area.config(state='normal')       # Возможность редактирования текстового поля
        self.output_area.insert(tk.END, text + "\n")  # Добавление нового текста в конец поля
        self.output_area.config(state='disabled')     # Снимается возможность редактирования текстового поля
        self.output_area.see(tk.END)                  # Прокручивает текстовое поле к концу

    def on_enter(self, event=None):
        command = self.input_entry.get().strip()      # Получение текста из поля ввода и удаление пробелов
        if not command:
            return

        self.history.append(command)                  # Добавление команды в историю
        self.history_index = len(self.history)        # Установка индекса
        self.display_output(f"> {command}")           # Показывает команду в фрейме вывода
        self.execute_command(command)                 # Передает команду на выполнение
        self.input_entry.delete(0, tk.END)       # Очищение поля ввода

    def execute_command(self, command_line):
        parts = self._split_and_expand(command_line)  # Используем метод с раскрытием переменных
        if not parts:
            return
        command = parts[0]                            # Первое слово - имя команды
        args = parts[1:]                              # Срез со второго - аргументы

        raw = command_line.strip()                    # Специальная обработка для случаев, когда введена только переменная
        if len(parts) == 1:
            if raw.startswith('~') or raw.startswith('$'):
                self.display_output(parts[0])
                return

        # Обработчик команд
        if command == "ls":
            self.command_ls(args)
        elif command == "cd":
            self.command_cd(args)
        elif command == "history":
            self.command_history(args)
        elif command == "du":
            self.command_du(args)
        elif command == "rm":
            self.command_rm(args)
        elif command == "chmod":
            self.command_chmod(args)
        elif command == "exit":
            self.quit()
        else:
            self.display_output(f"Command not found: {command}")

    # ЭТАП 2: Выполнение стартового скрипта
    def run_startup_script(self):
        try:
            with open(self.startup_script, 'r') as f:      # Открываем стартовый скрипт на чтение
                for line in f:
                    line = line.strip()                    # Удаляем символы в начале и конце строки
                    if line and not line.startswith('#'):  # Если строка есть и это не комментарий
                        self.display_output(f"> {line}")   # Выводим
                        self.history.append(line)
                        self.history_index = len(self.history)
                        self.execute_command(line)         # Команда выполняется
        except Exception as e:                             # Если встречается исключение (ошибка)
            self.display_output(f"Script error: {e}")

    def load_vfs(self, zip_path): # Загружаем VFS из ZIP-архива в память
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:                      # Раскрываем зип в режиме чтения
                all_paths = zip_ref.namelist()                                         # Список всех файлов в папке архива
                if not all_paths:
                    self.display_output("Empty VFS archive")                           # Пустой архив
                    return
                common_prefix = os.path.commonprefix(all_paths)                        # Находим общий префикс
                if common_prefix and not common_prefix.endswith('/'):                  # Если префикс не заканчивается на /
                    common_prefix = common_prefix.rsplit('/', 1)[0] + '/' # Обрезаем до последней /

                for file_info in zip_ref.infolist():                                   # Проходим по всем элементам архива
                    file_path = file_info.filename                                     # Получаем полный путь в архиве
                    if common_prefix and file_path.startswith(common_prefix):          # Есть ли префикс и начинается ли путь с него
                        file_path = file_path[len(common_prefix):]                     # Удаляем общий префикс из пути
                    if not file_path:                                                  # Пустой путь
                        continue
                    if file_info.is_dir():                                             # Если элемент - директория
                        if not file_path.endswith('/'):                                # Если путь не заканчивается / - добавляем его
                            file_path += '/'
                        dir_name = "/" + file_path.rstrip('/') if file_path.rstrip('/') else "/" # Нормализированное имя директории
                        self.dirs.add(dir_name)                                        # Добавляем директорию в список
                    else:
                        with zip_ref.open(file_info) as file:                          # Если не директория - открываем файл в архиве
                            content = file.read()
                        try:
                            content_str = content.decode('utf-8')                      # Декодируем текст
                            file_path_with_slash = "/" + file_path if file_path else "/" # Создаем путь с ведущим /
                            self.files[file_path_with_slash] = content_str             # Добавляем файл в список
                            self.file_permissions[file_path_with_slash] = '644'        # Устанавливаем права доступа
                        except UnicodeDecodeError:                                     # Если файл бинарный
                            content_b64 = base64.b64encode(content).decode('utf-8')    # Декодируем
                            file_path_with_slash = "/" + file_path if file_path else "/" # Создаем путь с ведущим /
                            self.files[file_path_with_slash] = content_b64             # Добавляем файл в список
                            self.file_permissions[file_path_with_slash] = '644'        # Устанавливаем права доступа

                    dir_path = os.path.dirname(file_path) or ""                        # Получаем путь к родительской директории
                    if dir_path:
                        full_dir_path = "/" + dir_path                                 # Добавляем ведущий слеш
                        self.dirs.add(full_dir_path)                                   # Добавляем родительскую директорию в список
                self.dirs.add("/")                                                     # Добавляем корневую директорию
                self.display_output(f"VFS loaded from {zip_path}")

        except FileNotFoundError:
            self.display_output(f"Error: VFS file not found: {zip_path}")
        except zipfile.BadZipFile:
            self.display_output(f"Error: Invalid ZIP format: {zip_path}")

    # === ЭТАП 4: Основные команды ===
    def normalize_path(self, path, current_dir=None): # Нормализация путей
        if current_dir is None:                       # Если не указана текущая директория
            current_dir = self.current_dir            # Используем текущую рабочую директорию эмулятора
        if path.startswith("/"):                      # Если это абсолютный путь (начинается с /)
            normalized = path
        else:                                         # Относительный путь
            if current_dir == "/":                    # Если текущая директория корень
                normalized = "/" + path               # Добавляем путь к корню
            else:
                normalized = current_dir + "/" + path # Объединяем текущую директорию и путь
        parts = []                                    # Список для хранения частей пути
        for part in normalized.split('/'):
            if part == "..":
                if parts:
                    parts.pop()                       # Удаляем последнюю добавленную часть пути
            elif part and part != ".":
                parts.append(part)                    # Добавляем корректную часть пути в список

        result = "/" + "/".join(parts) if parts else "/"
        return result

    def list_dir(self, path):
        normalized_path = self.normalize_path(path)             # Нормализуем путь
        files = []
        dirs = []
        for file_path in self.files.keys():                     # Проходим по всем файлам в vfs
            file_dir = os.path.dirname(file_path) or "/"        # Извлекаем путь к директории файла
            if file_dir == normalized_path:                     # Если файл находится в нужной директории
                files.append(os.path.basename(file_path))       # Добавляем имя файла в список
        for dir_path in self.dirs:                              # Проходим по всем директориям в vfs
            if dir_path != normalized_path and dir_path != "/": # Исключаем целевую и корневую директорию
                parent_dir = os.path.dirname(dir_path) or "/"   # Родительская директория
                if parent_dir == normalized_path:               # Если поддиректория находится в нужной директории
                    dirs.append(os.path.basename(dir_path))
        return sorted(dirs), sorted(files)

    def command_ls(self, args):
        path = args[0] if args else "."                         # Определяем путь для отображения
        try:
            dirs, files = self.list_dir(path)                   # Получаем списки
            normalized_path = self.normalize_path(path)         # Нормализуем путь
            self.display_output(f"Directory: {normalized_path}")
            for d in dirs:
                self.display_output(f"  {d}/")
            for f in files:                                     # Формируем полный путь для проверки прав доступа
                if normalized_path == "/":                      # Если путь - корневая директория
                    full_file_path = f"/{f}"                    # Создаем путь с ведущим /
                else:
                    full_file_path = f"{normalized_path}/{f}"
                if full_file_path in self.file_permissions:     # Если файл в словаре прав доступа
                    perms = self.file_permissions[full_file_path] # Получаем права доступа
                    self.display_output(f"{perms} {f}")
                else:
                    self.display_output(f"  {f}")
            if not dirs and not files:
                self.display_output("  (empty)")
        except Exception as e:
            self.display_output(f"ls: {path}: No such directory - {e}")

    def command_cd(self, args):
        if not args:
            self.current_dir = "/"
        else:
            path = args[0]                                             # Извлекает первый аргумент как путь
            normalized_path = self.normalize_path(path)                # Нормализует путь
            if normalized_path in self.dirs or normalized_path == "/": # Если путь в списке или корневая директория
                self.current_dir = normalized_path                     # Объявляем текущую директорию
            else:
                self.display_output(f"cd: {path}: No such directory")
                return
        self.display_output(f"Current directory: {self.current_dir}")

    def command_history(self, args):
        if not self.history:                          # Если история пустая
            self.display_output("history: no history available")
        else:
            for i, cmd in enumerate(self.history, 1): # Проходим по всем командам истории
                self.display_output(f"{i:4}  {cmd}")  # Индекс и команда

    def command_du(self, args):
        path = args[0] if args else self.current_dir  # Определяем путь
        normalized_path = self.normalize_path(path)   # Нормализуем путь
        total_size = 0                                # Общий размер файлов
        files_found = False

        for file_path, content in self.files.items():     # Проходим по парам путь/содержимое из словаря файлов
            file_dir = os.path.dirname(file_path) or "/"  # Получаем путь к директории
            if file_dir == normalized_path:               # Если файл находится в нормализированной директории
                file_size = len(content)
                total_size += file_size
                files_found = True
                self.display_output(f"{file_size:8}  {os.path.basename(file_path)}")  # Информация о файле

        dirs_found = False
        for dir_path in self.dirs:
            if dir_path != normalized_path and dir_path != "/": # Исключаем целевую и корневую директорию
                parent_dir = os.path.dirname(dir_path) or "/"
                if parent_dir == normalized_path:
                    dir_size = 4096                             # Минимальный размер директории
                    total_size += dir_size
                    dirs_found = True
                    self.display_output(f"{dir_size:8}  {os.path.basename(dir_path)}/")

        if files_found or dirs_found:
            self.display_output(f"{total_size:8}  .")
        else:
            self.display_output(f"{total_size:8}  .  (empty)")

    def command_rm(self, args):
        if not args:
            self.display_output("rm: missing operand")
            return
        filename = args[0]                           # Первый аргумент - имя файла
        full_path = self.normalize_path(filename)    # Нормализуем путь

        # Проверяем существование файла
        if full_path in self.files:                   # Если путь есть в списке файлов
            del self.files[full_path]                 # Удаляем запись
            if full_path in self.file_permissions:    # Если есть запись о правах доступа
                del self.file_permissions[full_path]  # Удаляем эту запись
            self.display_output(f"Removed file: {filename}")
        else:
            self.display_output(f"rm: cannot remove '{filename}': No such file")

    def command_chmod(self, args):
        if len(args) < 2: # Проверяем что минимум два аргумента
            self.display_output("usage: chmod [-Rv] mode file...")
            return
        mode = args[0]                                # Право доступа
        filename = args[1]                            # Имя файла
        full_path = self.normalize_path(filename)     # Нормализуем путь
        if full_path not in self.files:               # Если файла нет в списке
            self.display_output(f"chmod: cannot access '{filename}': No such file or directory")
            return
        if not re.match(r'^[0-7]{3}$', mode): # Проверяем, что число состоит из 3 цифр
            self.display_output(f"chmod: invalid mode: '{mode}'")
            self.display_output("Try 'chmod 755 file' or 'chmod 644 file'")
            return
        for digit in mode:                           # Дополнительная проверка диапазона чисел
            if int(digit) > 7:
                self.display_output(f"chmod: invalid mode: '{mode}'")
                self.display_output("Each digit must be between 0 and 7")
                return
        self.file_permissions[full_path] = mode

if __name__ == "__main__":
    app = ShellEmulator()
    app.mainloop()