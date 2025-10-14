import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import re
import base64
from tkinter import PhotoImage

# --- функции ---
def center_window(win, width, height):
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def update_format_options():
    if mode.get() == "audio":
        format_menu['values'] = ["mp3", "wav", "aac", "flac", "opus"]
        format_var.set("mp3")
        resolution_menu.config(state="disabled")
        resolution_var.set("лучшее")
        cover_menu.config(state="readonly")
        if cover_var.get() not in ("с обложкой", "без обложки"):
            cover_var.set("с обложкой")
    else:
        format_menu['values'] = ["mp4", "webm", "mkv"]
        format_var.set("mp4")
        resolution_menu.config(state="readonly")
        cover_var.set("без обложки")
        cover_menu.config(state="disabled")


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        save_path.set(folder)


def custom_confirm(title, message):
    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg="#3b4252")
    win.iconphoto(True, icon_image)
    win.resizable(False, False)
    w, h = 320, 130
    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    x = root_x + (root_w // 2) - (w // 2)
    y = root_y + (root_h // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.grab_set()
    tk.Label(win, text=message, pady=15, bg="#3b4252", fg="#eceff4").pack()
    result = {"answer": None}

    def on_yes():
        result["answer"] = True
        win.destroy()

    def on_no():
        result["answer"] = False
        win.destroy()

    btn_frame = tk.Frame(win, bg="#3b4252")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Да", width=10, bg="#a3be8c", fg="#2e3440", activebackground="#81a662", activeforeground="#2e3440", command=on_yes).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Нет", width=10, bg="#bf616a", fg="#2e3440", activebackground="#a4424c", activeforeground="#2e3440", command=on_no).pack(side=tk.LEFT, padx=10)
    win.wait_window()
    return result["answer"]


def copy_paste(event):
    if event.state & 0x4:
        if event.keycode == 86 and event.keysym != 'v':
            event.widget.event_generate('<<Paste>>')
        elif event.keycode == 67 and event.keysym != 'c':
            event.widget.event_generate('<<Copy>>')
        elif event.keycode == 88 and event.keysym != 'x':
            event.widget.event_generate('<<Cut>>')


def show_context_menu(event):
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Вставить", command=lambda: event.widget.event_generate('<<Paste>>'))
    menu.tk_popup(event.x_root, event.y_root)


def limit_entry_size(*args):
    value = url_var.get()
    if len(value) > 199:
        url_var.set(value[:199])


def set_widgets_state(state):
    """Блокировка/разблокировка всех элементов"""
    # Entry для ссылки
    url_entry.config(state=state)

    # Combobox — всегда readonly при разблокировке
    if state == "disabled":
        format_menu.config(state="disabled")
        cover_menu.config(state="disabled")
        resolution_menu.config(state="disabled")
    else:
        format_menu.config(state="readonly" if mode.get() == "video" else "disabled")
        cover_menu.config(state="readonly" if mode.get() == "audio" else "disabled")
        resolution_menu.config(state="readonly" if mode.get() == "video" else "disabled")

    # Радиокнопки и кнопки
    for rb in frame_mode.winfo_children():
        rb.config(state=state)
    btn_download.config(state=state)
    btn_folder.config(state=state)

    # Лог всегда только для программного вывода
    log_text.config(state="disabled")


def check_for_updates():
    set_widgets_state("disabled")
    log_text.config(state="normal")
    log_text.insert(tk.END, ">>> Проверка обновлений yt-dlp...\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")
    try:
        process = subprocess.Popen(
            ["yt-dlp", "-U"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in process.stdout:
            log_text.config(state="normal")
            log_text.insert(tk.END, line)
            log_text.see(tk.END)
            log_text.config(state="disabled")
        process.wait()
        log_text.config(state="normal")
        log_text.insert(tk.END, ">>> Проверка обновлений завершена.\n\n")
        log_text.see(tk.END)
        log_text.config(state="disabled")
    except Exception as e:
        log_text.config(state="normal")
        log_text.insert(tk.END, f"[ОШИБКА] Не удалось проверить обновления: {e}\n")
        log_text.see(tk.END)
        log_text.config(state="disabled")
    finally:
        set_widgets_state("normal")


def download_stub():
    log_text.config(state="normal")
    log_text.delete("1.0", tk.END)
    log_text.config(state="disabled")
    progress_var.set(0)
    log_text.config(state="normal")
    log_text.insert(tk.END, "=== Настройки загрузки ===\n")
    log_text.insert(tk.END, f"Ссылка: {url_entry.get()}\n")
    log_text.insert(tk.END, f"Режим: {mode.get()}\n")
    log_text.insert(tk.END, f"Формат: {format_var.get()}\n")
    log_text.insert(tk.END, f"Обложка: {cover_var.get()}\n")
    log_text.insert(tk.END, f"Разрешение: {resolution_var.get()}\n")
    log_text.insert(tk.END, f"Папка сохранения: {save_path.get() if save_path.get() else 'не выбрана'}\n")
    log_text.insert(tk.END, "===========================\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")
    answer = custom_confirm("Подтверждение", "Запустить загрузку?")
    if answer:
        start_download()


def start_download():
    url = url_entry.get().strip()
    if not url:
        log_text.config(state="normal")
        log_text.insert(tk.END, "\n[ОШИБКА] Введите ссылку для загрузки!\n")
        log_text.see(tk.END)
        log_text.config(state="disabled")
        return

    out_folder = save_path.get() if save_path.get() else os.getcwd()
    mode_choice = mode.get()
    fmt = format_var.get()
    res = resolution_var.get()
    cover_choice = cover_var.get()
    cmd = ["yt-dlp", url, "-P", out_folder, "--newline"]

    if mode_choice == "audio":
        cmd += ["-x", "--audio-format", fmt, "--audio-quality", "0", "-f", "bestaudio"]
        if cover_choice == "с обложкой":
            cmd.append("--embed-thumbnail")
            cmd.append("--add-metadata")
    else:
        if res != "лучшее":
            cmd += ["-f", f"bestvideo[height<={res.replace('p', '')}]+bestaudio/best[height<={res.replace('p', '')}]"]
        else:
            cmd += ["-f", "bestvideo+bestaudio/best"]
        cmd += ["--recode-video", fmt]

    threading.Thread(target=run_download, args=(cmd,), daemon=True).start()


def run_download(cmd):
    progress_var.set(0)
    log_text.config(state="normal")
    log_text.insert(tk.END, f"\n>>> Запуск: {' '.join(cmd)}\n\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        for line in process.stdout:
            log_text.config(state="normal")
            log_text.insert(tk.END, line)
            log_text.see(tk.END)
            log_text.config(state="disabled")
            match = re.search(r"(\d{1,3}(?:\.\d)?)%", line)
            if match:
                try:
                    progress_var.set(float(match.group(1)))
                except:
                    pass
        process.wait()

        log_text.config(state="normal")
        if process.returncode == 0:
            progress_var.set(100)
            log_text.insert(tk.END, "\n=== Загрузка завершена ===\n")
            log_text.see(tk.END)
            messagebox.showinfo("YT-DLP", "Загрузка завершена!")
        else:
            log_text.insert(tk.END, "\n[ОШИБКА] Файл не был скачан!\n")
            log_text.see(tk.END)
            messagebox.showerror("YT-DLP", "Ошибка: файл не был скачан!")
        log_text.config(state="disabled")

    except Exception as e:
        log_text.config(state="normal")
        log_text.insert(tk.END, f"\n[ИСКЛЮЧЕНИЕ] {e}\n")
        log_text.see(tk.END)
        log_text.config(state="disabled")
        messagebox.showerror("YT-DLP", f"Ошибка: {e}")


# --- интерфейс ---
root = tk.Tk()
root.title("ytGrabbie")
root.configure(bg="#3b4252")
center_window(root, 600, 500)
root.minsize(600, 500)

# --- Встроенная иконка ---
ICON_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAACQ0lEQVR4nO2Yu2sUURjFTyImwSKSCGJja6GoRUDU+b4kapMiYiFpLCyiEV9gaSdCRA2xyT+QIo9GsVGiATHgu1C08IGPShK08RVxCUbYI3fcWXRJnJnM3Z0ZvT84sAyz3z2HOzP33g9wOBwOh+N/gLuwih4208NuKo5TMUDBGAUTFNyn4AUF76j45EswRwV9/fodXDf3PKfgnv9fxSgF56g45tc2Y2xFa3LDQD0FfRRMUVEom6mdCqWxDxKoi2d+PRoomEzBNBfRNbZhefQAggsZMM0KDUQz34EmCr5kwDArNMs2rAgP4KEzA2a5oNqxI0qA3tSN6iIS9EV5/vtTN6oJ3gMKxhMN8vAGuX9DtWbgcpQAtxINYvgxT14aIrtW2g7xJEqAx4kDBMx+IIdOkB31tgLMhAdQvLIWIODlI/LIdhsBvoeuyial9QCGYpGcukjuXZssRBcawx6hz1UJEDD3jRw+Te5sXFr9LWgOm4H5qgYImHlDnuqJX38bVmcjwPRr8mR3/PqCljw/QkX2YFl6L/HkCLlnzdJrK77+1XzmP6OC6douZB/fk4OH7C1kgqc13ko02zGuZd2t/mbuwQS5b51t4yzNwHi+t9OC/nwfaDz05vtI6aHz3z/UGygYzIBhVug8YjW2FNczYJq+TAsyTmPLDwHUUXEg5dbiTf+jEre1uGAgQQvbsZGCbioOU3GGihEqrlBw26ySVLwtN3H/DF347bq55xkVd6i4WmrunqXgqF9bsMlKc9fhcDgcDuSAn9VThUlTulWSAAAAAElFTkSuQmCC
"""
icon_data = base64.b64decode(ICON_B64)
icon_image = PhotoImage(data=icon_data)

# --- Применение иконки ---
root.iconphoto(True, icon_image)

# --- Настройка стилей ttk ---
style = ttk.Style()
style.theme_use('clam')
style.configure("TCombobox",
                fieldbackground="#d8dee9",
                background="#8fbcbb",
                foreground="#2e3440")
style.map("TCombobox",
          fieldbackground=[("disabled", "#4c566a")],  # фон текстового поля при блокировке
          foreground=[("disabled", "#d8dee9")],       # текст при блокировке
          arrowcolor=[("disabled", "#2e3440")],       # стрелка при блокировке
          background=[("disabled", "#bf616a")])       # фон вокруг стрелки при блокировке
style.configure("TProgressbar",
                troughcolor="#4c566a",
                background="#a3be8c")

# --- URL ---
frame_url = tk.Frame(root, bg="#3b4252")
frame_url.pack(pady=10, fill=tk.X, padx=8)
tk.Label(frame_url, text="Ссылка:", bg="#3b4252", fg="#d8dee9").pack(side=tk.LEFT)
url_var = tk.StringVar()
url_var.trace_add('write', limit_entry_size)
url_entry = tk.Entry(frame_url, bg="#d8dee9", fg="#3b4252", disabledbackground="#4c566a", disabledforeground="#eceff4", insertbackground="#3b4252",
                     width=55, font=("Segoe UI", 10), textvariable=url_var)
url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
save_path = tk.StringVar()
btn_folder = tk.Button(frame_url, text="...", bg="#4c566a", fg="#d8dee9", activebackground="#3b4252", activeforeground="#d8dee9", width=3, command=choose_folder)
btn_folder.pack(side=tk.LEFT)
url_entry.bind("<Control-Key>", copy_paste)
url_entry.bind("<Button-3>", show_context_menu)

# --- Режим ---
mode = tk.StringVar(value="video")
frame_mode = tk.Frame(root, bg="#3b4252")
frame_mode.pack(pady=10)
tk.Radiobutton(frame_mode, text="Видео", variable=mode, value="video",
               bg="#3b4252", fg="#d8dee9", selectcolor="#3b4252", activebackground="#3b4252", activeforeground="#d8dee9", command=update_format_options).pack(side=tk.LEFT,
                                                                                                      padx=8)
tk.Radiobutton(frame_mode, text="Аудио", variable=mode, value="audio",
               bg="#3b4252", fg="#d8dee9", selectcolor="#3b4252", activebackground="#3b4252", activeforeground="#d8dee9", command=update_format_options).pack(side=tk.LEFT,
                                                                                                      padx=8)

# --- Формат и Обложка ---
frame_format = tk.Frame(root, bg="#3b4252")
frame_format.pack(pady=10)
tk.Label(frame_format, text="Формат:", bg="#3b4252", fg="#eceff4").pack(side=tk.LEFT, padx=5)
format_var = tk.StringVar(value="mp4")
format_menu = ttk.Combobox(frame_format, textvariable=format_var, values=["mp4", "webm", "mkv"],
                           state="readonly", width=15)
format_menu.pack(side=tk.LEFT, padx=5)
format_menu.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())
cover_var = tk.StringVar(value="с обложкой")
cover_menu = ttk.Combobox(frame_format, textvariable=cover_var,
                          values=["без обложки", "с обложкой"], state="readonly", width=12)
cover_menu.pack(side=tk.LEFT, padx=5)
cover_menu.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())

# --- Разрешение ---
frame_res = tk.Frame(root, bg="#3b4252")
frame_res.pack(pady=10)
tk.Label(frame_res, text="Разрешение:", bg="#3b4252", fg="#eceff4").pack(side=tk.LEFT, padx=5)
resolution_var = tk.StringVar(value="лучшее")
resolution_menu = ttk.Combobox(frame_res, textvariable=resolution_var,
                               values=["лучшее", "1080p", "720p", "480p", "360p"], state="readonly", width=10)
resolution_menu.pack(side=tk.LEFT, padx=5)
resolution_menu.bind("<<ComboboxSelected>>", lambda e: e.widget.selection_clear())

# --- Скачать ---
btn_download = tk.Button(root, text="Скачать", command=download_stub,
                         bg="#81a1c1", fg="#2e3440", activebackground="#5e81ac", activeforeground="#2e3440", width=20)
btn_download.pack(pady=16)

# --- Прогресс ---
tk.Label(root, text="Прогресс:", bg="#3b4252", fg="#eceff4").pack(pady=3)
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill=tk.X, padx=8, pady=8)

# --- Лог ---
tk.Label(root, text="Лог:", bg="#3b4252", fg="#eceff4").pack(pady=3)
log_text = tk.Text(root, height=18, bg="#4c566a", fg="#eceff4", insertbackground="#d8dee9")
log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
log_text.config(state="disabled")  # только для программного вывода

update_format_options()

# --- Проверка обновлений при запуске ---
threading.Thread(target=check_for_updates, daemon=True).start()

root.mainloop()
