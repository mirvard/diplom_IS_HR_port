import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
import csv


def init_database():
    conn = sqlite3.connect("hr_port.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_time TEXT,
            action_text TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            position TEXT NOT NULL,
            cert_expiry TEXT,
            phone TEXT,
            address TEXT,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES Categories(id)
        )
    """)

    try:
        cursor.execute("ALTER TABLE Employees ADD COLUMN phone TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE Employees ADD COLUMN address TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE Logs ADD COLUMN user_id INTEGER")
    except:
        pass

    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (username, password) VALUES ('admin', 'admin')")

        categories = ['Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
                      'Технічний та обслуговуючий персонал', 'Логістичний персонал']
        for cat in categories:
            cursor.execute("INSERT INTO Categories (name) VALUES (?)", (cat,))

        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, phone, address, category_id) VALUES ('Іванов Петро Іванович', '1985-04-12', 'Чоловіча', 'Начальник порту', '2028-10-20', '+380501234567', 'м. Одеса, вул. Морська, 1', 1)")
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, phone, address, category_id) VALUES ('Панков Михайло Романович', '2004-05-12', 'Чоловіча', 'Капітан далекого плавання', '2026-07-05', '+380677654321', 'м. Одеса, вул. Портова, 5', 2)")
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, phone, address, category_id) VALUES ('Шевченко Ольга Іванівна', '1990-11-23', 'Жіноча', 'Диспетчер', '2025-12-30', '+380931112233', 'м. Одеса, пр. Шевченка, 12', 5)")

    conn.commit()
    conn.close()


def log_action(text, user_id=None):
    conn = sqlite3.connect("hr_port.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO Logs (action_time, action_text, user_id) VALUES (?, ?, ?)", (now, text, user_id))
    conn.commit()
    conn.close()


class HRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ІС Відділу кадрів морського порту")
        self.root.geometry("400x250")
        self.current_user_id = None
        self.create_login_screen()

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
        tk.Button(self.login_frame, text="Увійти", command=self.check_login, bg="#2b5797", fg="white", width=15).pack(pady=15)

    def check_login(self):
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?",
                       (self.entry_user.get(), self.entry_pass.get()))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.current_user_id = user[0]
            log_action(f"Користувач {self.entry_user.get()} увійшов у систему", self.current_user_id)
            self.login_frame.destroy()
            self.create_main_screen()
        else:
            messagebox.showerror("Помилка", "Невірний логін або пароль")

    def create_main_screen(self):
        self.root.geometry("1300x550")

        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="Служба:", font=("Arial", 10, "bold")).pack(side="left")
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(top_frame, textvariable=self.cat_var, state="readonly", width=30)
        self.cat_combo['values'] = ('Всі категорії', 'Керівництво та Адміністрація', 'Служба капітана порту',
                                    'Виробничий персонал', 'Технічний та обслуговуючий персонал', 'Логістичний персонал')
        self.cat_combo.current(0)
        self.cat_combo.pack(side="left", padx=10)
        self.cat_combo.bind("<<ComboboxSelected>>", self.load_data)

        tk.Button(top_frame, text="Експорт звіту (CSV)", bg="#2b5797", fg="white", command=self.export_to_csv).pack(side="left", padx=5)
        tk.Button(top_frame, text="+ Нова справа", bg="#107c41", fg="white", command=self.open_add_window).pack(side="right")
        tk.Button(top_frame, text="- Видалити", bg="#a80000", fg="white", command=self.delete_employee).pack(side="right", padx=10)

        columns = ("id", "name", "birth", "gender", "position", "expiry", "phone", "address", "category")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="ПІБ")
        self.tree.heading("birth", text="Дата нар.")
        self.tree.heading("gender", text="Стать")
        self.tree.heading("position", text="Посада")
        self.tree.heading("expiry", text="Сертифікат до")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("address", text="Адреса")
        self.tree.heading("category", text="Служба")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("birth", width=90, anchor="center")
        self.tree.column("gender", width=70, anchor="center")
        self.tree.column("position", width=160)
        self.tree.column("expiry", width=110, anchor="center")
        self.tree.column("phone", width=120, anchor="center")
        self.tree.column("address", width=200)
        self.tree.column("category", width=180)

        self.tree.tag_configure('expired', background='#ffcccc')
        self.tree.tag_configure('warning', background='#fff3cd')

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.load_data()

    def load_data(self, event=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        selected_cat = self.cat_var.get()
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()

        query = """SELECT E.id, E.full_name, E.birth_date, E.gender, E.position, 
                          E.cert_expiry, E.phone, E.address, C.name 
                   FROM Employees E JOIN Categories C ON E.category_id = C.id"""
        params = ()
        if selected_cat != 'Всі категорії':
            query += " WHERE C.name = ?"
            params = (selected_cat,)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        today = datetime.now().date()
        warning_limit = today + timedelta(days=30)

        for row in rows:
            expiry_date_str = row[5]
            tag = ''
            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                if expiry_date < today:
                    tag = 'expired'
                elif expiry_date < warning_limit:
                    tag = 'warning'
            except (ValueError, TypeError):
                pass
            self.tree.insert("", "end", values=row, tags=(tag,))
        conn.close()

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "ПІБ", "Дата народження", "Стать", "Посада", "Сертифікат до", "Телефон", "Адреса", "Служба"])
                for row_id in self.tree.get_children():
                    writer.writerow(self.tree.item(row_id)['values'])
            messagebox.showinfo("Успіх", f"Звіт збережено у файл:\n{file_path}")
            log_action("Згенеровано звіт у форматі CSV", self.current_user_id)

    def open_add_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Нова справа")
        add_win.geometry("400x500")

        tk.Label(add_win, text="ПІБ:").pack()
        en_name = tk.Entry(add_win, width=40)
        en_name.pack()

        tk.Label(add_win, text="Дата народження (РРРР-ММ-ДД):").pack()
        en_birth = tk.Entry(add_win, width=40)
        en_birth.pack()

        tk.Label(add_win, text="Посада:").pack()
        en_pos = tk.Entry(add_win, width=40)
        en_pos.pack()

        tk.Label(add_win, text="Сертифікат до (РРРР-ММ-ДД):").pack()
        en_cert = tk.Entry(add_win, width=40)
        en_cert.pack()

        tk.Label(add_win, text="Телефон (наприклад +380501234567):").pack()
        en_phone = tk.Entry(add_win, width=40)
        en_phone.pack()

        tk.Label(add_win, text="Адреса проживання:").pack()
        en_address = tk.Entry(add_win, width=40)
        en_address.pack()

        tk.Label(add_win, text="Категорія:").pack()
        cb_cat = ttk.Combobox(add_win, values=['Керівництво та Адміністрація', 'Служба капітана порту',
                              'Виробничий персонал', 'Технічний та обслуговуючий персонал',
                              'Логістичний персонал'], state="readonly", width=37)
        cb_cat.current(0)
        cb_cat.pack()

        def save():
            if not en_name.get().strip():
                messagebox.showerror("Помилка", "Поле ПІБ не може бути порожнім")
                return
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Categories WHERE name=?", (cb_cat.get(),))
            result = cursor.fetchone()
            if result is None:
                messagebox.showerror("Помилка", "Категорію не знайдено")
                conn.close()
                return
            c_id = result[0]
            cursor.execute(
                "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, phone, address, category_id) VALUES (?,?,?,?,?,?,?,?)",
                (en_name.get(), en_birth.get(), "Чоловіча", en_pos.get(), en_cert.get(),
                 en_phone.get(), en_address.get(), c_id))
            conn.commit()
            conn.close()
            log_action(f"Додано нового працівника: {en_name.get()}", self.current_user_id)
            self.load_data()
            add_win.destroy()

        tk.Button(add_win, text="Зберегти", command=save, bg="#107c41", fg="white").pack(pady=20)

    def delete_employee(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected, "values")
        if messagebox.askyesno("Підтвердження", f"Видалити {item[1]}?"):
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Employees WHERE id=?", (item[0],))
            conn.commit()
            conn.close()
            log_action(f"Видалено працівника з ID: {item[0]}", self.current_user_id)
            self.load_data()


if __name__ == "__main__":
    init_database()
    root = tk.Tk()
    app = HRApp(root)
    root.mainloop()