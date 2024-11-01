import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import sys
import subprocess
import threading


class ImageInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Inspector")
        self.root.geometry("950x650")
        self.root.config(bg="#2c3e50")  # Темный фон для всего приложения

        # Настройка стиля
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview", background="#34495e", foreground="white", rowheight=30, fieldbackground="#34495e")
        style.map("Treeview", background=[("selected", "#1abc9c")])
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), foreground="white", background="#1abc9c")

        # Путь к изображению и панель выбора
        self.create_folder_selection_panel()

        # Панель с таблицей
        self.create_treeview_panel()

    def create_folder_selection_panel(self):
        # Панель для выбора папки
        panel = tk.Frame(self.root, bg="#2c3e50", pady=10)
        panel.pack(fill=tk.X, padx=20)

        tk.Label(panel, text="Select Folder:", font=("Arial", 12, "bold"), fg="white", bg="#2c3e50").pack(side=tk.LEFT,
                                                                                                          padx=10)

        # Поле ввода пути к папке
        self.folder_path = tk.StringVar()
        entry = tk.Entry(panel, textvariable=self.folder_path, font=("Arial", 10), width=40, bd=2, relief=tk.GROOVE)
        entry.pack(side=tk.LEFT, padx=5)

        # Кнопка "Browse"
        browse_button = tk.Button(panel, text="Browse", command=self.select_folder, font=("Arial", 10), bg="#1abc9c",
                                  fg="white", bd=0, padx=15)
        browse_button.pack(side=tk.LEFT, padx=10)

        # Кнопка "Scan Images"
        scan_button = tk.Button(panel, text="Scan Images", command=self.scan_images, font=("Arial", 10), bg="#e74c3c",
                                fg="white", bd=0, padx=15)
        scan_button.pack(side=tk.LEFT)

    def create_treeview_panel(self):
        # Основная панель для таблицы с прокрутками
        tree_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("Filename", "Dimensions", "Resolution", "Color Depth", "Compression")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")

        # Настройка столбцов и заголовков
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=160)

        # Прокрутки
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)

        # Размещение таблицы и прокруток
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Связь с событием двойного щелчка для открытия изображений
        self.tree.bind("<Double-1>", self.open_image)

        # Хранение путей к изображениям
        self.file_paths = {}

    def select_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.folder_path.set(selected_folder)

    def scan_images(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder to scan.")
            return

        # Очистка данных
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_paths.clear()

        # Запуск обработки изображений в отдельном потоке
        threading.Thread(target=self.process_images, args=(folder,), daemon=True).start()

    def process_images(self, folder):
        supported_formats = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png')
        image_files = [os.path.join(root, file)
                       for root, _, files in os.walk(folder)
                       for file in files if file.lower().endswith(supported_formats)]

        if not image_files:
            messagebox.showinfo("No Images Found", "No supported image files were found in the selected folder.")
            return

        for file_path in image_files:
            try:
                with Image.open(file_path) as img:
                    filename = os.path.basename(file_path)
                    dimensions = f"{img.width} x {img.height}"
                    dpi = img.info.get('dpi', (0, 0))
                    resolution = f"{dpi[0]} x {dpi[1]}"
                    color_depth = self.get_color_depth(img)
                    compression = img.info.get('compression', 'None')

                    # Добавление в таблицу
                    item_id = self.tree.insert('', 'end',
                                               values=(filename, dimensions, resolution, color_depth, compression))
                    self.file_paths[item_id] = file_path

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    def get_color_depth(self, img):
        mode_to_bpp = {
            "1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32, "CMYK": 32, "YCbCr": 24,
            "LAB": 24, "HSV": 24, "I": 32, "F": 32,
        }
        return f"{mode_to_bpp.get(img.mode, 'Unknown')} bits"

    def open_image(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            file_path = self.file_paths.get(selected_item)
            if file_path:
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(file_path)
                    elif sys.platform.startswith("darwin"):
                        subprocess.call(["open", file_path])
                    elif sys.platform.startswith("linux"):
                        subprocess.call(["xdg-open", file_path])
                    else:
                        messagebox.showerror("Error", "Unsupported operating system.")
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot open file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageInspectorApp(root)
    root.mainloop()
