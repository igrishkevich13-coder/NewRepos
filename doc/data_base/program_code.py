import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


class LibraryDB:
    def __init__(self, db_name: str = 'library.db'):
        self.db_name = db_name
        
    def get_connection(self):
        """Получение нового соединения с базой данных"""
        conn = sqlite3.connect(self.db_name)
        return conn


class LibraryManager:
    def __init__(self, db_name: str = 'library.db'):
        self.db_name = db_name
        self._create_tables()
        self._insert_initial_data()
        
    def _create_tables(self):
        """Создание таблиц базы данных"""
        conn = LibraryDB(self.db_name).get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Books (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER,
            Name TEXT NOT NULL,
            Status BOOLEAN DEFAULT 0,
            FOREIGN KEY(Booking_ID) REFERENCES Booking(ID) ON DELETE SET NULL
        );
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Readers (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            LastName TEXT NOT NULL,
            FirstName TEXT NOT NULL,
            Patronimus TEXT NOT NULL,
            Contacts TEXT NOT NULL
        );
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Booking (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Reader_ID INTEGER NOT NULL,
            DateOfTaking TEXT NOT NULL,
            DateOfReturn TEXT NOT NULL,
            FOREIGN KEY(Reader_ID) REFERENCES Readers(ID) ON DELETE CASCADE
        );
        ''')
        
        conn.commit()
        conn.close()
        
    def _insert_initial_data(self):
        """Вставка начальных данных"""
        conn = LibraryDB(self.db_name).get_connection()
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже данные в таблице Readers
        cursor.execute("SELECT COUNT(*) FROM Readers")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Добавляем читателей
            readers = [
                ('Иваненко', 'Иван', 'Иванович', 'mail1@mail.ru'),
                ('Иваненко', 'Анна', 'Ивановна', 'mail2@mail.ru'),
                ('Петров', 'Пётр', 'Петрович', 'mail3@mail.ru'),
                ('Николаев', 'Николай', 'Николаевич', 'mail4@mail.ru'),
                ('Васильев', 'Василий', 'Васильевич', 'mail5@mail.ru')
            ]
            
            cursor.executemany(
                "INSERT INTO Readers (LastName, FirstName, Patronimus, Contacts) VALUES (?, ?, ?, ?)",
                readers
            )
            
            # Добавляем книги
            cursor.execute("INSERT INTO Books (Name, Booking_ID, Status) VALUES ('Война и мир', 1, 1)")
            cursor.execute("INSERT INTO Books (Name, Booking_ID, Status) VALUES ('Мёртвые души', 2, 1)")
            cursor.execute("INSERT INTO Books (Name, Booking_ID, Status) VALUES ('Гроза', 3, 1)")
            cursor.execute("INSERT INTO Books (Name, Booking_ID, Status) VALUES ('Недоросль', 4, 1)")
            cursor.execute("INSERT INTO Books (Name, Booking_ID, Status) VALUES ('Горе от ума', 5, 1)")
            cursor.execute("INSERT INTO Books (Name) VALUES ('Евгений Онегин')")
            cursor.execute("INSERT INTO Books (Name) VALUES ('Герой нашего времени')")
            cursor.execute("INSERT INTO Books (Name) VALUES ('Отцы и дети')")
            cursor.execute("INSERT INTO Books (Name) VALUES ('Преступление и наказание')")
            cursor.execute("INSERT INTO Books (Name) VALUES ('Тихий Дон')")
            
            # Добавляем бронирования
            bookings = [
                (1, '01.12.2025', '14.12.2025'),
                (2, '01.12.2025', '14.12.2025'),
                (3, '01.12.2025', '14.12.2025'),
                (4, '01.12.2025', '14.12.2025'),
                (5, '01.12.2025', '14.12.2025')
            ]
            
            cursor.executemany(
                "INSERT INTO Booking (Reader_ID, DateOfTaking, DateOfReturn) VALUES (?, ?, ?)",
                bookings
            )
            
            conn.commit()
        conn.close()
        
    def _execute_query(self, query: str, params: tuple = (), fetch: bool = False, fetch_all: bool = False):
        """Универсальный метод выполнения запросов"""
        conn = LibraryDB(self.db_name).get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchone()
            elif fetch_all:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
            else:
                result = cursor.lastrowid
            
            conn.commit()
            return result
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # === CRUD операции для книг ===
    def add_book(self, name: str) -> int:
        """Добавление новой книги"""
        return self._execute_query(
            "INSERT INTO Books (Name) VALUES (?)",
            (name,)
        )
            
    def get_all_books(self) -> List[Dict[str, Any]]:
        """Получение всех книг с информацией о читателе"""
        query = """
            SELECT b.*, 
                   r.LastName || ' ' || r.FirstName || ' ' || r.Patronimus as ReaderName,
                   bk.DateOfReturn
            FROM Books b
            LEFT JOIN Booking bk ON b.Booking_ID = bk.ID
            LEFT JOIN Readers r ON bk.Reader_ID = r.ID
            ORDER BY b.ID
        """
        return self._execute_query(query, fetch_all=True)
            
    def get_available_books(self) -> List[Dict[str, Any]]:
        """Получение доступных для выдачи книг"""
        return self._execute_query(
            "SELECT * FROM Books WHERE Status = 0 OR Status IS NULL ORDER BY ID",
            fetch_all=True
        )
            
    def update_book_status(self, book_id: int, status: bool, booking_id: Optional[int] = None):
        """Обновление статуса книги"""
        if booking_id is not None:
            self._execute_query(
                "UPDATE Books SET Status = ?, Booking_ID = ? WHERE ID = ?",
                (1 if status else 0, booking_id, book_id)
            )
        else:
            self._execute_query(
                "UPDATE Books SET Status = ?, Booking_ID = NULL WHERE ID = ?",
                (1 if status else 0, book_id)
            )
            
    def delete_book(self, book_id: int):
        """Удаление книги"""
        self._execute_query("DELETE FROM Books WHERE ID = ?", (book_id,))
            
    # === CRUD операции для читателей ===
    def add_reader(self, last_name: str, first_name: str, patronimus: str, contacts: str) -> int:
        """Добавление нового читателя"""
        return self._execute_query(
            "INSERT INTO Readers (LastName, FirstName, Patronimus, Contacts) VALUES (?, ?, ?, ?)",
            (last_name, first_name, patronimus, contacts)
        )
            
    def get_all_readers(self) -> List[Dict[str, Any]]:
        """Получение всех читателей"""
        return self._execute_query("SELECT * FROM Readers ORDER BY ID", fetch_all=True)
            
    def get_reader_books(self, reader_id: int) -> List[Dict[str, Any]]:
        """Получение книг, взятых читателем"""
        query = """
            SELECT b.* FROM Books b
            JOIN Booking bk ON b.Booking_ID = bk.ID
            WHERE bk.Reader_ID = ? AND b.Status = 1
            ORDER BY b.ID
        """
        return self._execute_query(query, (reader_id,), fetch_all=True)
            
    # === Операции с бронированиями ===
    def create_booking(self, reader_id: int, book_id: int, 
                      date_of_taking: str, date_of_return: str) -> int:
        """Создание бронирования книги"""
        # Проверяем, доступна ли книга
        books = self.get_available_books()
        available_book_ids = [book['ID'] for book in books]
        
        if book_id not in available_book_ids:
            raise ValueError(f"Книга с ID {book_id} недоступна для выдачи")
        
        # Создаем бронирование
        booking_id = self._execute_query(
            "INSERT INTO Booking (Reader_ID, DateOfTaking, DateOfReturn) VALUES (?, ?, ?)",
            (reader_id, date_of_taking, date_of_return)
        )
        
        # Обновляем статус книги
        self.update_book_status(book_id, True, booking_id)
        
        return booking_id
            
    def return_book(self, book_id: int):
        """Возврат книги в библиотеку"""
        # Получаем ID бронирования для этой книги
        result = self._execute_query(
            "SELECT Booking_ID FROM Books WHERE ID = ?",
            (book_id,),
            fetch=True
        )
        
        if result and result[0]:
            # Удаляем бронирование
            self._execute_query("DELETE FROM Booking WHERE ID = ?", (result[0],))
            
            # Обновляем статус книги
            self.update_book_status(book_id, False, None)
            
    def get_overdue_books(self) -> List[Dict[str, Any]]:
        """Получение просроченных книг"""
        current_date = datetime.now().strftime('%d.%m.%Y')
        # Упрощенный запрос без преобразования дат
        query = """
            SELECT b.Name, 
                   r.LastName || ' ' || r.FirstName as ReaderName, 
                   bk.DateOfReturn
            FROM Books b
            JOIN Booking bk ON b.Booking_ID = bk.ID
            JOIN Readers r ON bk.Reader_ID = r.ID
            WHERE b.Status = 1
        """
        
        all_books = self._execute_query(query, fetch_all=True)
        
        # Фильтруем в коде Python для простоты
        overdue_books = []
        for book in all_books:
            # Простая проверка даты (формат DD.MM.YYYY)
            return_date = book['DateOfReturn']
            try:
                return_day = int(return_date.split('.')[0])
                return_month = int(return_date.split('.')[1])
                return_year = int(return_date.split('.')[2])
                
                current_day = int(current_date.split('.')[0])
                current_month = int(current_date.split('.')[1])
                current_year = int(current_date.split('.')[2])
                
                # Сравниваем даты
                if (current_year > return_year or
                    (current_year == return_year and current_month > return_month) or
                    (current_year == return_year and current_month == return_month and current_day > return_day)):
                    overdue_books.append(book)
            except:
                continue
                
        return overdue_books
    
    def search_books(self, search_term: str) -> List[Dict[str, Any]]:
        """Поиск книг по названию"""
        return self._execute_query(
            "SELECT * FROM Books WHERE Name LIKE ? ORDER BY ID",
            (f'%{search_term}%',),
            fetch_all=True
        )
    
    def search_readers(self, search_term: str) -> List[Dict[str, Any]]:
        """Поиск читателей по ФИО"""
        query = """
            SELECT * FROM Readers 
            WHERE LastName LIKE ? OR FirstName LIKE ? OR Patronimus LIKE ?
            ORDER BY LastName, FirstName
        """
        return self._execute_query(
            query,
            (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'),
            fetch_all=True
        )


# === Пример использования ===
def main():
    # Создаем менеджер библиотеки
    library = LibraryManager()
    
    print("=== Все книги ===")
    books = library.get_all_books()
    for book in books:
        status = "Выдана" if book['Status'] == 1 else "Доступна"
        reader = book.get('ReaderName', 'Нет')
        print(f"{book['ID']}. {book['Name']} - {status} (Читатель: {reader})")
    
    print("\n=== Доступные книги ===")
    available_books = library.get_available_books()
    if available_books:
        for book in available_books:
            print(f"{book['ID']}. {book['Name']}")
    else:
        print("Нет доступных книг")
    
    print("\n=== Все читатели ===")
    readers = library.get_all_readers()
    for reader in readers:
        print(f"{reader['ID']}. {reader['LastName']} {reader['FirstName']} {reader['Patronimus']}")
    
    # Пример: выдача книги
    print("\n=== Выдача книги ===")
    if available_books:
        book_id = available_books[0]['ID']
        reader_id = 1
        
        try:
            booking_id = library.create_booking(
                reader_id=reader_id,
                book_id=book_id,
                date_of_taking='10.12.2025',
                date_of_return='24.12.2025'
            )
            print(f"Книга выдана. ID бронирования: {booking_id}")
        except ValueError as e:
            print(f"Ошибка: {e}")
    
    # Пример: возврат книги
    print("\n=== Возврат книги ===")
    library.return_book(book_id=1)
    print(f"Книга с ID {1} возвращена")
    
    # Пример: поиск книг
    print("\n=== Поиск книг по названию 'мир' ===")
    found_books = library.search_books("мир")
    for book in found_books:
        print(f"{book['ID']}. {book['Name']}")


def interactive_menu():
    """Интерактивное меню для работы с библиотекой"""
    library = LibraryManager()
    
    while True:
        print("\n" + "="*50)
        print("БИБЛИОТЕЧНАЯ СИСТЕМА")
        print("="*50)
        print("1. Показать все книги")
        print("2. Показать доступные книги")
        print("3. Показать всех читателей")
        print("4. Выдать книгу (используется номер читателя, поэтому перед этим выполните 3.)")
        print("5. Вернуть книгу (используется номер книги, поэтому перед этим выполните 1.)")
        print("6. Показать просроченные книги")
        print("7. Добавить новую книгу")
        print("8. Добавить нового читателя")
        print("9. Поиск книг")
        print("10. Поиск читателей")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            books = library.get_all_books()
            print("\nСписок всех книг:")
            for book in books:
                status = "✓ Выдана" if book['Status'] == 1 else "✓ Доступна"
                reader = book.get('ReaderName', 'Нет')
                print(f"{book['ID']:3}. {book['Name']:30} - {status:15} Читатель: {reader}")
                
        elif choice == "2":
            books = library.get_available_books()
            print("\nДоступные книги:")
            if books:
                for book in books:
                    print(f"{book['ID']:3}. {book['Name']}")
            else:
                print("Нет доступных книг")
                
        elif choice == "3":
            readers = library.get_all_readers()
            print("\nСписок всех читателей:")
            for reader in readers:
                print(f"{reader['ID']:3}. {reader['LastName']} {reader['FirstName']} {reader['Patronimus']}")
                
        elif choice == "4":
            print("\nВыдача книги:")
            available_books = library.get_available_books()
            if not available_books:
                print("Нет доступных книг для выдачи")
                continue
                
            print("Доступные книги:")
            for book in available_books:
                print(f"{book['ID']}. {book['Name']}")
                
            try:
                book_id = int(input("Введите ID книги: "))
                reader_id = int(input("Введите ID читателя: "))
                date_of_taking = input("Дата выдачи (ДД.ММ.ГГГГ): ")
                date_of_return = input("Дата возврата (ДД.ММ.ГГГГ): ")
                
                booking_id = library.create_booking(
                    reader_id=reader_id,
                    book_id=book_id,
                    date_of_taking=date_of_taking,
                    date_of_return=date_of_return
                )
                print(f"Книга успешно выдана! ID бронирования: {booking_id}")
            except ValueError as e:
                print(f"Ошибка: {e}")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                
        elif choice == "5":
            print("\nВозврат книги:")
            try:
                book_id = int(input("Введите ID возвращаемой книги: "))
                library.return_book(book_id)
                print("Книга успешно возвращена!")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                
        elif choice == "6":
            overdue_books = library.get_overdue_books()
            print("\nПросроченные книги:")
            if overdue_books:
                for book in overdue_books:
                    print(f"{book['Name']} - Читатель: {book['ReaderName']}, Дата возврата: {book['DateOfReturn']}")
            else:
                print("Нет просроченных книг")
                
        elif choice == "7":
            print("\nДобавление новой книги:")
            name = input("Введите название книги: ")
            if name:
                book_id = library.add_book(name)
                print(f"Книга добавлена! ID: {book_id}")
            else:
                print("Название книги не может быть пустым")
                
        elif choice == "8":
            print("\nДобавление нового читателя:")
            last_name = input("Фамилия: ")
            first_name = input("Имя: ")
            patronimus = input("Отчество: ")
            contacts = input("Контакты: ")
            
            if last_name and first_name:
                reader_id = library.add_reader(last_name, first_name, patronimus, contacts)
                print(f"Читатель добавлен! ID: {reader_id}")
            else:
                print("Фамилия и имя обязательны")
                
        elif choice == "9":
            search_term = input("\nВведите текст для поиска книг: ")
            found_books = library.search_books(search_term)
            print(f"\nНайдено книг: {len(found_books)}")
            for book in found_books:
                status = "Выдана" if book['Status'] == 1 else "Доступна"
                print(f"{book['ID']}. {book['Name']} - {status}")
                
        elif choice == "10":
            search_term = input("\nВведите текст для поиска читателей: ")
            found_readers = library.search_readers(search_term)
            print(f"\nНайдено читателей: {len(found_readers)}")
            for reader in found_readers:
                print(f"{reader['ID']}. {reader['LastName']} {reader['FirstName']} {reader['Patronimus']}")
                
        elif choice == "0":
            print("Выход из программы...")
            break
            
        else:
            print("Неверный выбор. Попробуйте еще раз.")


if __name__ == "__main__":
    # Для быстрого теста раскомментируйте:
    # main()
    
    # Для интерактивного режима:
    interactive_menu()