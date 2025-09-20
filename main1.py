import tkinter as tk
from tkinter import scrolledtext
import os
import getpass
import platform


class ShellEmulator(tk.Tk):
    def __init__(self):                     #конструктор класса
        super().__init__()                  #вызывает конструктор родительского класса
        self.current_dir = os.getcwd()      #cохраняет текущую рабочую директорию в переменную экземпляра
        self._setup_ui()                    #метод для создания и настройки пользовательского интерфейса
        self._display_welcome()             #метод для отображения приветственного сообщения.

    def _setup_ui(self):                                  #метод для создания и настройки пользовательского интерфейса
        username = getpass.getuser()
        hostname = platform.node()
        self.title(f"Эмулятор - [{username}@{hostname}]")
        self.geometry("800x600")

        # Область вывода
        self.output_area = scrolledtext.ScrolledText(
            self, state='disabled', wrap='word',
            bg='black', fg='white', font=('Consolas', 12)
        )
        self.output_area.pack(expand=True, fill='both', padx=5, pady=5)

        # Фрейм для ввода
        input_frame = tk.Frame(self, bg='black')
        input_frame.pack(fill='x', padx=5, pady=(0, 5))

        # Приглашение командной строки
        self.prompt_label = tk.Label(
            input_frame,
            text=self._get_prompt(),
            fg='green', bg='black', font=('Consolas', 12)
        )
        self.prompt_label.pack(side='left')

        # Поле ввода команды
        self.input_entry = tk.Entry(
            input_frame, bg='black', fg='white',
            insertbackground='white', font=('Consolas', 12),
            width=50
        )
        self.input_entry.pack(side='left', expand=True, fill='x', padx=(5, 0))
        self.input_entry.focus_set()
        self.input_entry.bind("<Return>", self._on_enter)

    def _get_prompt(self):
        username = getpass.getuser()
        hostname = platform.node()
        dir_name = os.path.basename(self.current_dir)
        return f"{username}@{hostname}:{dir_name}$ "

    def _display_welcome(self):
        self._display_output("Добро пожаловать в эмулятор командной строки!")
        self._display_output("Доступные команды: ls, cd, exit")
        self._display_output("Поддерживается раскрытие переменных окружения ($HOME, $USER, etc.)")
        self._display_output("-" * 50)

    def _display_output(self, text):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.config(state='disabled')
        self.output_area.see(tk.END)

    def _expand_variables(self, text):
        """Раскрытие переменных окружения"""
        result = text
        for var_name in os.environ:
            result = result.replace(f"${var_name}", os.environ[var_name])
            result = result.replace(f"${{{var_name}}}", os.environ[var_name])
        return result

    def _on_enter(self, event=None):
        command_text = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        if not command_text:
            return

        # Выводим команду с приглашением
        self._display_output(self._get_prompt() + command_text)

        # Раскрываем переменные окружения
        expanded_command = self._expand_variables(command_text)

        # Разбиваем на команду и аргументы
        parts = expanded_command.split()
        if not parts:
            return

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Выполняем команды-заглушки
        if command == "exit":
            self.quit()
        elif command == "ls":
            self._display_output(f"ls вызван с аргументами: {args}")
            self._display_output("file1.txt  file2.txt  directory/")
        elif command == "cd":
            self._display_output(f"cd вызван с аргументами: {args}")
            if args:
                self._display_output(f"Переход в директорию: {args[0]}")
            else:
                self._display_output("Переход в домашнюю директорию")
        else:
            self._display_output(f"{command}: команда не найдена")

        # Обновляем приглашение
        self.prompt_label.config(text=self._get_prompt())


if __name__ == "__main__":
    app = ShellEmulator()
    app.mainloop()