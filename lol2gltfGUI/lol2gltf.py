import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import webbrowser
import struct
from functools import partial

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("lol2gltf GUI")
        self.root.resizable(False, False)
        self.materials = []  # Список для хранения материалов
        self.material_fields = []  # Список для хранения ссылок на дополнительные поля
        self.ENTRY_WIDTH = 50  # Ширина полей ввода
        self.create_widgets()
        self.create_footer()  # Создаем нижние элементы сразу

    def create_widgets(self):
        """Создает основные элементы интерфейса."""
        self.create_selection_field(
            label_text="Path to the Simple Skin (.skn) file:",
            row=0,
            filetypes=[("SKN files", "*.skn")],
            callback=self.on_skn_file_selected
        )
        self.create_selection_field(
            label_text="Path to the Skeleton (.skl) file:",
            row=2,
            filetypes=[("SKL files", "*.skl")]
        )
        self.create_selection_field(
            label_text="Path to a folder containing Animation (.anm) files:",
            row=4,
            is_directory=True
        )
        self.create_selection_field(
            label_text="Path for the output glTF Binary (.glb) file:",
            row=6,
            is_directory=True
        )

    def create_selection_field(self, label_text, row, filetypes=None, is_directory=False, callback=None):
        """
        Создает поле для выбора файла или директории.
        
        :param label_text: Текст метки.
        :param row: Строка для размещения элементов.
        :param filetypes: Типы файлов (для выбора файла).
        :param is_directory: Если True, выбирается директория.
        :param callback: Функция обратного вызова при выборе файла.
        """
        tk.Label(self.root, text=label_text).grid(row=row, column=0, padx=5, pady=0, sticky="w")
        entry = tk.Entry(self.root, width=self.ENTRY_WIDTH)
        entry.grid(row=row + 1, column=0, padx=5, pady=0)
        tk.Button(
            self.root,
            text=". . .",
            command=partial(self.handle_file_or_dir, "select", entry, filetypes=filetypes, is_directory=is_directory, callback=callback)
        ).grid(row=row + 1, column=1, padx=5, pady=0)
        tk.Button(
            self.root,
            text="R",
            command=partial(self.handle_file_or_dir, "reset", entry, callback=callback)
        ).grid(row=row + 1, column=2, padx=5, pady=0)
        setattr(self, f"entry_{row}", entry)

    def create_footer(self):
        """Создает нижние элементы (версия, кнопка Convert, ссылка)."""
        self.footer_row = 8  # Начальная строка для нижних элементов
        self.version_label = tk.Label(
            self.root, text="Version 1.00",
            fg="blue", cursor="hand2",
            font=("Arial", 10, "underline")
        )
        self.version_label.grid(row=self.footer_row, column=0, padx=5, pady=5, sticky="w")
        self.version_label.bind("<Button-1>", self.show_version_info)

        self.convert_button = tk.Button(self.root, text="Convert", command=self.convert_to_glb)
        self.convert_button.grid(row=self.footer_row, column=0, padx=5, pady=5)

        self.link_label = self.create_link_label(
            text="© 2025 RedBear",
            row=self.footer_row,
            column=0,
            url="https://www.youtube.com/@TrueRedBear"
        )

    def create_link_label(self, text, row, column, url):
        """Создает метку с текстом в виде кликабельной ссылки."""
        link_label = tk.Label(
            self.root,
            text=text,
            fg="blue", cursor="hand2",
            font=("Arial", 10, "underline")
        )
        link_label.grid(row=row, column=column, padx=0, pady=5, sticky="e")
        link_label.bind("<Button-1>", lambda event: self.open_link(url))
        return link_label

    def handle_file_or_dir(self, action=None, entry_widget=None, filetypes=None, is_directory=False, callback=None):
        """Обрабатывает выбор файла или директории."""
        if action == "select":
            path = filedialog.askdirectory() if is_directory else filedialog.askopenfilename(filetypes=filetypes)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)
            if callback:
                callback(path)
        elif action == "reset":
            entry_widget.delete(0, tk.END)
            if callback:
                callback(None)

    def validate_paths(self, skn_path, skl_path, glb_dir):
        """Проверяет, что все необходимые пути указаны и корректны."""
        if not skn_path or not os.path.exists(skn_path):
            messagebox.showerror("Error", "Please select a valid .skn file.")
            return False
        if not skl_path or not os.path.exists(skl_path):
            messagebox.showerror("Error", "Please select a valid .skl file.")
            return False
        if not glb_dir:
            messagebox.showerror("Error", "Please select a path for the output .glb file.")
            return False
        if not os.path.exists(glb_dir):
            try:
                os.makedirs(glb_dir)
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create output directory: {e}")
                return False
        if not os.path.exists("lol2gltf.exe") or not os.access("lol2gltf.exe", os.X_OK):
            messagebox.showerror("Error", "lol2gltf.exe is missing or not executable.")
            return False
        return True

    def convert_to_glb(self):
        """Выполняет конвертацию в .glb файл."""
        skn_path = self.entry_0.get()
        skl_path = self.entry_2.get()
        anm_dir = self.entry_4.get()
        glb_dir = self.entry_6.get()

        if not self.validate_paths(skn_path, skl_path, glb_dir):
            return

        try:
            glb_filename = os.path.splitext(os.path.basename(skn_path))[0] + ".glb"
            glb_path = os.path.join(glb_dir, glb_filename)

            # Собираем список путей к текстурам и соответствующих материалов
            mat_names = []
            tex_paths = []
            for material, (_, entry, _, _) in zip(self.materials, self.material_fields):
                if entry.get():  # Если текстура выбрана
                    mat_names.append(material)
                    tex_paths.append(entry.get())

            # Формируем основную команду
            command = [
                "lol2gltf", "skn2gltf",
                "-m", skn_path,
                "-s", skl_path,
                "-g", glb_path
            ]

            # Расширяем основную команду, если выбраны анимации
            if anm_dir:
                command.extend(["-a", anm_dir])
            
            # Расширяем основную команду, если выбраны текстуры
            if mat_names:
                command.extend(["--materials"] + mat_names)
                command.extend(["--textures"] + tex_paths)

            # Запускаем итоговую команду
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", "Conversion completed successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error during conversion: {e}\nCommand: {' '.join(command)}")

    def open_link(self, url):
        """Открывает ссылку в браузере."""
        webbrowser.open(url)

    def on_skn_file_selected(self, skn_path):
        """Обрабатывает выбор .skn файла и создает дополнительные поля для материалов."""
        if skn_path:  # Если файл выбран
            self.materials = self.get_materials(skn_path)
            if self.materials:
                self.create_material_fields()
                self.update_footer_position()
            else:
                messagebox.showwarning("Warning", "No materials found in the selected .skn file.")
        else:  # Если файл сброшен
            self.clear_material_fields()

    def get_materials(self, skn_path):
        """Извлекает материалы из .skn файла."""
        try:
            with open(skn_path, 'rb') as skn_file:
                skn_magic = struct.unpack('<I', skn_file.read(4))[0]
                if skn_magic != 0x00112233:
                    raise ValueError(f"Wrong signature SKN file: \"{hex(skn_magic)}\"")

                major = struct.unpack('<H', skn_file.read(2))[0]
                minor = struct.unpack('<H', skn_file.read(2))[0]

                if major not in {0, 2, 4} or minor != 1:
                    raise ValueError(f"Unsupported SKN file version: \"{major}.{minor}\"")

                materials = []
                if major == 0:
                    skn_file.seek(8, 1)
                    materials.append(os.path.splitext(os.path.basename(skn_path))[0])
                else:
                    num_meshes = struct.unpack('<I', skn_file.read(4))[0]
                    for _ in range(num_meshes):
                        material_name = skn_file.read(64).decode('utf-8').rstrip('\x00')
                        materials.append(material_name)
                        skn_file.seek(16, 1)

                return materials
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read SKN file: {e}")
            return []

    def create_material_fields(self):
        """Создает дополнительные поля для каждого материала."""
        self.clear_material_fields()
        row_offset = 8
        for i, material in enumerate(self.materials):
            label = tk.Label(self.root, text=f"Path to texture file for material '{material}':")
            label.grid(row=row_offset + i * 2, column=0, padx=5, pady=0, sticky="w")

            entry = tk.Entry(self.root, width=self.ENTRY_WIDTH)
            entry.grid(row=row_offset + i * 2 + 1, column=0, padx=5, pady=0)

            select_button = tk.Button(
                self.root,
                text=". . .",
                command=partial(self.handle_file_or_dir, "select", entry, filetypes=[("Texture files", "*.dds *.png *.tga")])
            )
            select_button.grid(row=row_offset + i * 2 + 1, column=1, padx=5, pady=0)

            reset_button = tk.Button(
                self.root,
                text="R",
                command=partial(self.handle_file_or_dir, "reset", entry)
            )
            reset_button.grid(row=row_offset + i * 2 + 1, column=2, padx=5, pady=0)

            self.material_fields.append((label, entry, select_button, reset_button))

    def clear_material_fields(self):
        """Удаляет все дополнительные поля для материалов."""
        for field in self.material_fields:
            for widget in field:
                widget.destroy()
        self.material_fields.clear()
        self.update_footer_position()

    def update_footer_position(self):
        """Обновляет положение нижних элементов (версия, кнопка Convert, ссылка)."""
        self.footer_row = 8 + len(self.material_fields) * 2
        self.version_label.grid(row=self.footer_row, column=0, padx=5, pady=5, sticky="w")
        self.convert_button.grid(row=self.footer_row, column=0, padx=5, pady=5)
        self.link_label.grid(row=self.footer_row, column=0, padx=0, pady=5, sticky="e")
    
    def show_version_info(self, event=None):
        """Открывает окно с информацией о версии и списком изменений."""
        version_window = tk.Toplevel(self.root)
        version_window.title("Release notes")
        version_window.resizable(False, False)
        version_window.minsize(300, 0)  # Устанавливаем минимальную ширину окна

        version_text = """
        Version 1.00 (March 20, 2025)
        -------------------------
        - Initial release.
        """

        version_label = tk.Label(
            version_window,
            text=version_text,
            justify="left",
            wraplength=250
        )
        version_label.pack(padx=10, pady=10)

        close_button = tk.Button(version_window, text="Close", command=version_window.destroy)
        close_button.pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()