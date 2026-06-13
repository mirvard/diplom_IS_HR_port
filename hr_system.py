import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


# =====================================================================
# 1. ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ (СТРОГО ЗА ТЗ)
# =====================================================================
def init_database():
    conn = sqlite3.connect("hr_port.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Таблиця користувачів (Парольний вхід)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Таблиця категорій/спеціальностей персоналу
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Таблиця працівників (Особова справа)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            position TEXT NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES Categories(id)
        )
    """)

    # Заповнення початковими даними, якщо база порожня
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (username, password) VALUES ('admin', 'admin123')")

        # 5 категорій з ТЗ керівника
        categories = [
            'Керівництво та Адміністрація',
            'Служба капітана порту',
            'Виробничий персонал',
            'Технічний та обслуговуючий персонал',
            'Логістичний персонал'
        ]
        for cat in categories:
            cursor.execute("INSERT INTO Categories (name) VALUES (?)", (cat,))

        # Тестові працівники
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, category_id) VALUES ('Іванов Петро Іванович', '1985-04-12', 'Чоловіча', 'Начальник порту', 1)")
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, category_id) VALUES ('Панков Михайло Романович', '2004-05-12', 'Чоловіча', 'Капітан далекого плавання', 2)")
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, category_id) VALUES ('Шевченко Ольга Іванівна', '1990-11-23', 'Жіноча', 'Диспетчер', 5)")

    conn.commit()
    conn.close()


# =====================================================================
# 2. ГРАФІЧНИЙ ІНТЕРФЕЙС
# =====================================================================
class HRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ІС Відділу кадрів морського порту")
        self.root.geometry("400x250")

        self.create_login_screen()

    # --- ЕКРАН ВХОДУ ---
    def create_login_screen(self):
        self.login_frame = tk.Frame(self.root, pady=30)
        self.login_frame.pack()

        tk.Label(self.login_frame, text="Вхід у систему", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(self.login_frame, text="Логін:").pack()
        self.entry_user = tk.Entry(self.login_frame)
        self.entry_user.pack()

        tk.Label(self.login_frame, text="Пароль:").pack()
        self.entry_pass = tk.Entry(self.login_frame, show="*")
        self.entry_pass.pack()

        tk.Button(self.login_frame, text="Увійти", command=self.check_login, bg="#2b5797", fg="white", width=15).pack(
            pady=15)

    def check_login(self):
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?",
                       (self.entry_user.get(), self.entry_pass.get()))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.login_frame.destroy()
            self.create_main_screen()
        else:
            messagebox.showerror("Помилка", "Невірний логін або пароль")

    # --- ГОЛОВНИЙ ЕКРАН ТА ТАБЛИЦЯ ---
    def create_main_screen(self):
        self.root.geometry("850x450")

        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="Вибір категорії персоналу:", font=("Arial", 10, "bold")).pack(side="left")

        # Випадаючий список категорій
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(top_frame, textvariable=self.cat_var, state="readonly", width=40)
        self.cat_combo['values'] = (
        'Всі категорії', 'Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
        'Технічний та обслуговуючий персонал', 'Логістичний персонал')
        self.cat_combo.current(0)
        self.cat_combo.pack(side="left", padx=10)
        self.cat_combo.bind("<<ComboboxSelected>>", self.load_data)

        tk.Button(top_frame, text="+ Вписати нову людину", bg="#107c41", fg="white", command=self.open_add_window).pack(
            side="right")

        tk.Button(top_frame, text="- Видалити обраного", bg="#a80000", fg="white", command=self.delete_employee).pack(
            side="right", padx=10)

        # Таблиця
        columns = ("id", "name", "birth", "gender", "position", "category")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="ПІБ Працівника")
        self.tree.heading("birth", text="Дата народження")
        self.tree.heading("gender", text="Стать")
        self.tree.heading("position", text="Посада")
        self.tree.heading("category", text="Категорія")

        self.tree.column("id", width=30, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("birth", width=110, anchor="center")
        self.tree.column("gender", width=80, anchor="center")
        self.tree.column("position", width=150)
        self.tree.column("category", width=200)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.load_data()

    def load_data(self, event=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        selected_cat = self.cat_var.get()
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()

        if selected_cat == 'Всі категорії':
            cursor.execute(
                "SELECT E.id, E.full_name, E.birth_date, E.gender, E.position, C.name FROM Employees E JOIN Categories C ON E.category_id = C.id")
        else:
            cursor.execute(
                "SELECT E.id, E.full_name, E.birth_date, E.gender, E.position, C.name FROM Employees E JOIN Categories C ON E.category_id = C.id WHERE C.name = ?",
                (selected_cat,))

        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

    # --- ВІКНО ДОДАВАННЯ ПРАЦІВНИКА ---
    def open_add_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Нова особова справа")
        add_win.geometry("350x300")
        add_win.transient(self.root)  # Прив'язка до головного вікна
        add_win.grab_set()

        tk.Label(add_win, text="ПІБ:").pack(pady=2)
        entry_name = tk.Entry(add_win, width=35)
        entry_name.pack()

        tk.Label(add_win, text="Дата народження (РРРР-ММ-ДД):").pack(pady=2)
        entry_birth = tk.Entry(add_win, width=35)
        entry_birth.pack()

        tk.Label(add_win, text="Стать:").pack(pady=2)
        combo_gender = ttk.Combobox(add_win, values=["Чоловіча", "Жіноча"], state="readonly", width=32)
        combo_gender.current(0)
        combo_gender.pack()

        tk.Label(add_win, text="Посада:").pack(pady=2)
        entry_pos = tk.Entry(add_win, width=35)
        entry_pos.pack()

        tk.Label(add_win, text="Категорія:").pack(pady=2)
        combo_cat = ttk.Combobox(add_win,
                                 values=['Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
                                         'Технічний та обслуговуючий персонал', 'Логістичний персонал'],
                                 state="readonly", width=32)
        combo_cat.current(2)
        combo_cat.pack()

        def save_employee():
            # Отримуємо ID категорії з бази
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Categories WHERE name=?", (combo_cat.get(),))
            cat_id = cursor.fetchone()[0]

            # Зберігаємо працівника
            cursor.execute(
                "INSERT INTO Employees (full_name, birth_date, gender, position, category_id) VALUES (?, ?, ?, ?, ?)",
                (entry_name.get(), entry_birth.get(), combo_gender.get(), entry_pos.get(), cat_id))
            conn.commit()
            conn.close()

            self.load_data()  # Оновлюємо головну таблицю
            add_win.destroy()  # Закриваємо віконце

        tk.Button(add_win, text="Зберегти", command=save_employee, bg="#107c41", fg="white", width=20).pack(pady=15)


if __name__ == "__main__":
    init_database()
    window = tk.Tk()
    app = HRApp(window)
    window.mainloop()


    # --- ФУНКЦІЯ ВИДАЛЕННЯ ПРАЦІВНИКА ---
    def delete_employee(self):
        # Отримуємо виділений рядок у таблиці
        selected_item = self.tree.selection()

        # Якщо нічого не виділено — показуємо попередження
        if not selected_item:
            messagebox.showwarning("Увага", "Будь ласка, спочатку виберіть працівника у таблиці кліком миші!")
            return

        # Витягуємо дані виділеного рядка (ID та ПІБ)
        item_values = self.tree.item(selected_item, "values")
        emp_id = item_values[0]
        emp_name = item_values[1]

        # Запитуємо підтвердження (захист від випадкового кліку)
        confirm = messagebox.askyesno("Підтвердження", f"Ви дійсно хочете видалити працівника:\n{emp_name}?")

        if confirm:
            # Видаляємо з бази даних
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Employees WHERE id = ?", (emp_id,))
            conn.commit()
            conn.close()

            # Оновлюємо таблицю на екрані
            self.load_data()
            messagebox.showinfo("Успіх", "Особову справу працівника успішно видалено з бази.")