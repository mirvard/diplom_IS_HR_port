import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
import csv  # Імпортував для експорту звітів, викладач просив додати


# =====================================================================
# 1. ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ (Моя локальна SQLite)
# =====================================================================
def init_database():
    # Підключаємось до бази. Якщо файлу немає - він створиться автоматично. Дуже зручно!
    conn = sqlite3.connect("hr_port.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")  # Вмикаємо підтримку зовнішніх ключів, щоб була цілісність

    # Таблиця для адмінів. Паролі поки не хешував, для прототипу диплома так ок.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Вирішив додати таблицю для логів, щоб було видно хто і що робив (аудит)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_time TEXT,
            action_text TEXT
        )
    """)

    # Довідник відділів порту
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Головна таблиця з персоналом. Додав поле cert_expiry для контролю допусків
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            position TEXT NOT NULL,
            cert_expiry TEXT, 
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES Categories(id)
        )
    """)

    # Заповнюємо базу початковими даними, якщо вона порожня
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        # Ставлю логін/пароль admin/admin щоб точно не помилитися від хвилювання на захисті 😅
        cursor.execute("INSERT INTO Users (username, password) VALUES ('admin', 'admin')")

        categories = ['Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
                      'Технічний та обслуговуючий персонал', 'Логістичний персонал']
        for cat in categories:
            cursor.execute("INSERT INTO Categories (name) VALUES (?)", (cat,))

        # ДЛЯ ПОКАЗУ НА ЗАХИСТІ: спеціально роблю різні дати, щоб показати всі 3 кольори таблиці

        # 1. БІЛИЙ (Все ок, сертифікат діє аж до 2028 року)
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, category_id) VALUES ('Іванов Петро Іванович', '1985-04-12', 'Чоловіча', 'Начальник порту', '2028-10-20', 1)")

        # 2. ЖОВТИЙ (Попередження. Термін до липня 2026, тобто менше місяця від сьогодні!)
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, category_id) VALUES ('Панков Михайло Романович', '2004-05-12', 'Чоловіча', 'Капітан далекого плавання', '2026-07-05', 2)")

        # 3. ЧЕРВОНИЙ (Прострочено. Дата з минулого 2025 року. Треба звільняти або штрафувати)
        cursor.execute(
            "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, category_id) VALUES ('Шевченко Ольга Іванівна', '1990-11-23', 'Жіноча', 'Диспетчер', '2025-12-30', 5) ")

    conn.commit()
    conn.close()


# Простенька функція для запису логів у базу
def log_action(text):
    conn = sqlite3.connect("hr_port.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO Logs (action_time, action_text) VALUES (?, ?)", (now, text))
    conn.commit()
    conn.close()


# =====================================================================
# 2. ГОЛОВНИЙ КЛАС ПРОГРАМИ (Інтерфейс на Tkinter)
# =====================================================================
class HRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ІС Відділу кадрів морського порту")
        self.root.geometry("400x250")
        self.create_login_screen()

    def create_login_screen(self):
        # Малюю вікно логіну
        self.login_frame = tk.Frame(self.root, pady=30)
        self.login_frame.pack()
        tk.Label(self.login_frame, text="Вхід у систему", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self.login_frame, text="Логін:").pack()
        self.entry_user = tk.Entry(self.login_frame)
        self.entry_user.pack()
        tk.Label(self.login_frame, text="Пароль:").pack()
        self.entry_pass = tk.Entry(self.login_frame, show="*")  # Зірочки замість тексту
        self.entry_pass.pack()
        tk.Button(self.login_frame, text="Увійти", command=self.check_login, bg="#2b5797", fg="white", width=15).pack(
            pady=15)

    def check_login(self):
        # Йдемо в базу перевіряти юзера
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?",
                       (self.entry_user.get(), self.entry_pass.get()))
        user = cursor.fetchone()
        conn.close()

        if user:
            log_action(f"Користувач {self.entry_user.get()} увійшов у систему")
            self.login_frame.destroy()  # Прибираємо вікно логіну
            self.create_main_screen()  # Запускаємо головну прогу
        else:
            messagebox.showerror("Помилка", "Невірний логін або пароль")

    def create_main_screen(self):
        self.root.geometry("1100x550")  # Зробив ширше вікно, щоб влізла колонка сертифікатів

        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill="x")

        # Випадаючий список для фільтрації
        tk.Label(top_frame, text="Служба:", font=("Arial", 10, "bold")).pack(side="left")
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(top_frame, textvariable=self.cat_var, state="readonly", width=30)
        self.cat_combo['values'] = (
        'Всі категорії', 'Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
        'Технічний та обслуговуючий персонал', 'Логістичний персонал')
        self.cat_combo.current(0)
        self.cat_combo.pack(side="left", padx=10)
        self.cat_combo.bind("<<ComboboxSelected>>", self.load_data)  # Якщо змінили вибір - оновлюємо таблицю

        # Панель кнопок
        tk.Button(top_frame, text="Експорт звіту (CSV)", bg="#2b5797", fg="white", command=self.export_to_csv).pack(
            side="left", padx=5)
        tk.Button(top_frame, text="+ Нова справа", bg="#107c41", fg="white", command=self.open_add_window).pack(
            side="right")
        tk.Button(top_frame, text="- Видалити", bg="#a80000", fg="white", command=self.delete_employee).pack(
            side="right", padx=10)

        # Налаштування таблиці (Treeview)
        columns = ("id", "name", "birth", "gender", "position", "expiry", "category")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="ПІБ")
        self.tree.heading("birth", text="Дата нар.")
        self.tree.heading("gender", text="Стать")
        self.tree.heading("position", text="Посада")
        self.tree.heading("expiry", text="Сертифікат до")
        self.tree.heading("category", text="Служба")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("expiry", width=120, anchor="center")
        self.tree.column("category", width=200)

        # ТЕ САМЕ КОЛЬОРОВЕ КОДУВАННЯ: налаштовуємо теги для кольорів
        self.tree.tag_configure('expired', background='#ffcccc')  # Світло-червоний
        self.tree.tag_configure('warning', background='#fff3cd')  # Жовтуватий

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.load_data()

    def load_data(self, event=None):
        # Очищаємо таблицю перед новим завантаженням
        for row in self.tree.get_children():
            self.tree.delete(row)

        selected_cat = self.cat_var.get()
        conn = sqlite3.connect("hr_port.db")
        cursor = conn.cursor()

        # Використовую JOIN щоб замість ID категорії виводилась красива назва
        query = "SELECT E.id, E.full_name, E.birth_date, E.gender, E.position, E.cert_expiry, C.name FROM Employees E JOIN Categories C ON E.category_id = C.id"
        if selected_cat != 'Всі категорії':
            query += f" WHERE C.name = '{selected_cat}'"

        cursor.execute(query)
        rows = cursor.fetchall()

        # Логіка визначення прострочених документів (рахуємо від сьогоднішнього дня)
        today = datetime.now().date()
        warning_limit = today + timedelta(days=30)  # Якщо залишилось менше 30 днів - буде тривога

        for row in rows:
            expiry_date_str = row[5]
            tag = ''
            try:
                # Перетворюємо рядок в об'єкт дати, щоб можна було їх порівнювати
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                if expiry_date < today:
                    tag = 'expired'  # Вже прострочено
                elif expiry_date < warning_limit:
                    tag = 'warning'  # Скоро закінчиться
            except:
                pass  # Якщо хтось ввів дату не по формату, просто ігноруємо, помилки не буде

            self.tree.insert("", "end", values=row, tags=(tag,))
        conn.close()

    def export_to_csv(self):
        # Генерація звіту. Дуже корисна фіча для діловодства
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "ПІБ", "Дата народження", "Стать", "Посада", "Сертифікат до", "Служба"])
                for row_id in self.tree.get_children():
                    writer.writerow(self.tree.item(row_id)['values'])
            messagebox.showinfo("Успіх", f"Звіт збережено у файл:\n{file_path}")
            log_action("Згенеровано звіт у форматі CSV")

    def open_add_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Нова справа")
        add_win.geometry("400x380")

        tk.Label(add_win, text="ПІБ:").pack()
        en_name = tk.Entry(add_win, width=40);
        en_name.pack()

        tk.Label(add_win, text="Дата народження (РРРР-ММ-ДД):").pack()
        en_birth = tk.Entry(add_win, width=40);
        en_birth.pack()

        tk.Label(add_win, text="Посада:").pack()
        en_pos = tk.Entry(add_win, width=40);
        en_pos.pack()

        tk.Label(add_win, text="Сертифікат до (РРРР-ММ-ДД):").pack()
        en_cert = tk.Entry(add_win, width=40);
        en_cert.pack()

        tk.Label(add_win, text="Категорія:").pack()
        cb_cat = ttk.Combobox(add_win,
                              values=['Керівництво та Адміністрація', 'Служба капітана порту', 'Виробничий персонал',
                                      'Технічний та обслуговуючий персонал', 'Логістичний персонал'], state="readonly",
                              width=37)
        cb_cat.current(0);
        cb_cat.pack()

        def save():
            # Записуємо нову людину. Знаходимо правильний category_id
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Categories WHERE name=?", (cb_cat.get(),))
            c_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO Employees (full_name, birth_date, gender, position, cert_expiry, category_id) VALUES (?,?,?,?,?,?)",
                (en_name.get(), en_birth.get(), "Чоловіча", en_pos.get(), en_cert.get(), c_id))
            conn.commit()
            conn.close()
            log_action(f"Додано нового працівника: {en_name.get()}")
            self.load_data()  # Одразу малюємо нові дані в таблиці
            add_win.destroy()

        tk.Button(add_win, text="Зберегти", command=save, bg="#107c41", fg="white").pack(pady=20)

    def delete_employee(self):
        # Захист від дурня: перепитуємо чи точно треба видаляти
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected, "values")
        if messagebox.askyesno("Підтвердження", f"Видалити {item[1]}?"):
            conn = sqlite3.connect("hr_port.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Employees WHERE id=?", (item[0],))
            conn.commit()
            conn.close()
            log_action(f"Видалено працівника з ID: {item[0]}")
            self.load_data()


if __name__ == "__main__":
    init_database()
    root = tk.Tk()
    app = HRApp(root)
    root.mainloop()