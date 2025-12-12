import sqlite3

# Создание базы данных (файл)
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Создание таблицы Books
cursor.execute('''
CREATE TABLE IF NOT EXISTS Books (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL
)
''')

# Добавление записи
cursor.execute("INSERT INTO Books (Name) VALUES ('Л.Н. Толстой')")

# Получение данных
cursor.execute("SELECT * FROM Books")
print(cursor.fetchall())

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()