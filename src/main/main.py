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
    
    def get_books_by_name(self, book_name: str, only_issued: bool = False) -> List[Dict[str, Any]]:
        """Поиск книг по названию"""
        if only_issued:
            query = """
                SELECT b.*, 
                       r.LastName || ' ' || r.FirstName || ' ' || r.Patronimus as ReaderName,
                       bk.DateOfReturn
                FROM Books b
                LEFT JOIN Booking bk ON b.Booking_ID = bk.ID
                LEFT JOIN Readers r ON bk.Reader_ID = r.ID
                WHERE b.Name LIKE ? AND b.Status = 1
                ORDER BY b.ID
            """
        else:
            query = """
                SELECT b.*, 
                       r.LastName || ' ' || r.FirstName || ' ' || r.Patronimus as ReaderName,
                       bk.DateOfReturn
                FROM Books b
                LEFT JOIN Booking bk ON b.Booking_ID = bk.ID
                LEFT JOIN Readers r ON bk.Reader_ID = r.ID
                WHERE b.Name LIKE ?
                ORDER BY b.ID
            """
        return self._execute_query(query, (f'%{book_name}%',), fetch_all=True)
            
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
    
    def find_reader_by_fio(self, last_name: str, first_name: str, patronimus: str = "") -> Optional[Dict[str, Any]]:
        """Поиск читателя по фамилии, имени и отчеству"""
        query = """
            SELECT * FROM Readers 
            WHERE LastName LIKE ? AND FirstName LIKE ?
        """
        
        if patronimus:
            query += " AND Patronimus LIKE ?"
            params = (f'%{last_name}%', f'%{first_name}%', f'%{patronimus}%')
        else:
            params = (f'%{last_name}%', f'%{first_name}%')
            
        readers = self._execute_query(query, params, fetch_all=True)
        
        if readers:
            # Возвращаем первого найденного читателя
            return readers[0]
        return None
            
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
            
    def return_book_by_id(self, book_id: int) -> bool:
        """Возврат книги по ID"""
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
            return True
        return False
    
    def return_book_by_name(self, book_name: str) -> Dict[str, Any]:
        """Возврат книги по названию"""
        # Ищем выданные книги с таким названием
        issued_books = self.get_books_by_name(book_name, only_issued=True)
        
        if not issued_books:
            return {'success': False, 'message': f'Нет выданных книг с названием "{book_name}"'}
        
        if len(issued_books) == 1:
            # Если найдена только одна книга, возвращаем ее
            book_id = issued_books[0]['ID']
            if self.return_book_by_id(book_id):
                return {
                    'success': True, 
                    'message': f'Книга "{issued_books[0]["Name"]}" успешно возвращена',
                    'book_id': book_id,
                    'book_name': issued_books[0]['Name']
                }
        
        # Если найдено несколько книг, возвращаем список для выбора
        return {
            'success': False, 
            'message': f'Найдено несколько выданных книг с названием "{book_name}"',
            'books': issued_books,
            'need_choice': True
        }
            
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


class ReaderInterface:
    """Интерфейс для читателя"""
    
    def __init__(self, library: LibraryManager):
        self.library = library
    
    def show_all_books(self):
        """Показать все книги"""
        books = self.library.get_all_books()
        print("\n" + "="*60)
        print("ВСЕ КНИГИ В БИБЛИОТЕКЕ")
        print("="*60)
        for book in books:
            status = "Выдана" if book['Status'] == 1 else "Доступна"
            reader = book.get('ReaderName', 'Нет')
            date_return = book.get('DateOfReturn', '')
            if status == "Выдана":
                print(f"{book['ID']:3}. {book['Name']:35} - {status:15} Читатель: {reader:20} Дата возврата: {date_return}")
            else:
                print(f"{book['ID']:3}. {book['Name']:35} - {status}")
    
    def show_available_books(self):
        """Показать доступные книги"""
        books = self.library.get_available_books()
        print("\n" + "="*50)
        print("ДОСТУПНЫЕ ДЛЯ ВЫДАЧИ КНИГИ")
        print("="*50)
        if books:
            for book in books:
                print(f"{book['ID']:3}. {book['Name']}")
        else:
            print("Нет доступных книг в данный момент")
    
    def return_book(self):
        """Вернуть книгу"""
        print("\n" + "="*40)
        print("ВОЗВРАТ КНИГИ")
        print("="*40)
        book_name = input("Введите название книги для возврата: ").strip()
        
        if not book_name:
            print("Название книги не может быть пустым")
            return
        
        result = self.library.return_book_by_name(book_name)
        
        if result['success']:
            print(f"\n{result['message']}")
        elif result.get('need_choice', False):
            print(f"\n{result['message']}")
            print("\nВыберите книгу для возврата:")
            
            books = result['books']
            for i, book in enumerate(books, 1):
                reader_name = book.get('ReaderName', 'Неизвестно')
                date_return = book.get('DateOfReturn', '')
                print(f"{i}. {book['Name']} (ID: {book['ID']}) - Читатель: {reader_name}, Дата возврата: {date_return}")
            
            try:
                choice_num = int(input("\nВведите номер книги для возврата (0 для отмены): "))
                
                if choice_num == 0:
                    print("Возврат отменен")
                    return
                
                if 1 <= choice_num <= len(books):
                    selected_book = books[choice_num - 1]
                    if self.library.return_book_by_id(selected_book['ID']):
                        print(f"Книга \"{selected_book['Name']}\" успешно возвращена")
                    else:
                        print("Ошибка при возврате книги")
                else:
                    print("Неверный номер книги")
            except ValueError:
                print("Пожалуйста, введите корректный номер")
        else:
            print(f"\n{result['message']}")
    
    def search_books(self):
        """Поиск книг"""
        print("\n" + "="*40)
        print("ПОИСК КНИГ")
        print("="*40)
        search_term = input("Введите текст для поиска книг: ")
        found_books = self.library.search_books(search_term)
        print(f"\nНайдено книг: {len(found_books)}")
        for book in found_books:
            status = "Выдана" if book['Status'] == 1 else "Доступна"
            print(f"{book['ID']}. {book['Name']} - {status}")
    
    def show_menu(self):
        """Показать меню читателя"""
        while True:
            print("\n" + "="*50)
            print("РЕЖИМ ЧИТАТЕЛЯ")
            print("="*50)
            print("1. Показать все книги")
            print("2. Показать доступные книги")
            print("3. Вернуть книгу")
            print("4. Поиск книг")
            print("0. Выйти в главное меню")
            
            choice = input("\nВыберите действие: ")
            
            if choice == "1":
                self.show_all_books()
            elif choice == "2":
                self.show_available_books()
            elif choice == "3":
                self.return_book()
            elif choice == "4":
                self.search_books()
            elif choice == "0":
                print("Выход из режима читателя...")
                break
            else:
                print("Неверный выбор. Попробуйте еще раз.")


class LibrarianInterface:
    """Интерфейс для библиотекаря"""
    
    def __init__(self, library: LibraryManager):
        self.library = library
    
    def show_all_readers(self):
        """Показать всех читателей"""
        readers = self.library.get_all_readers()
        print("\n" + "="*50)
        print("ВСЕ ЧИТАТЕЛИ")
        print("="*50)
        for reader in readers:
            print(f"{reader['ID']:3}. {reader['LastName']} {reader['FirstName']} {reader['Patronimus']} - {reader['Contacts']}")
    
    def issue_book(self):
        """Выдать книгу (поиск читателя по ФИО)"""
        print("\n" + "="*50)
        print("ВЫДАЧА КНИГИ")
        print("="*50)
        
        # Показать доступные книги
        available_books = self.library.get_available_books()
        if not available_books:
            print("Нет доступных книг для выдачи")
            return
            
        print("\nДоступные книги:")
        for book in available_books:
            print(f"{book['ID']}. {book['Name']}")
        
        try:
            book_id = int(input("\nВведите ID книги для выдачи: "))
            
            # Проверяем, что книга доступна
            available_book_ids = [book['ID'] for book in available_books]
            if book_id not in available_book_ids:
                print("Эта книга недоступна для выдачи")
                return
            
            # Поиск читателя по ФИО
            print("\nПоиск читателя:")
            last_name = input("Фамилия: ").strip()
            first_name = input("Имя: ").strip()
            patronimus = input("Отчество (можно пропустить): ").strip()
            
            reader = self.library.find_reader_by_fio(last_name, first_name, patronimus)
            
            if not reader:
                print(f"\nЧитатель {last_name} {first_name} {patronimus} не найден.")
                register = input("Хотите зарегистрировать нового читателя? (да/нет): ").lower()
                
                if register == 'да':
                    print("\nРегистрация нового читателя:")
                    new_last_name = input("Фамилия: ").strip()
                    new_first_name = input("Имя: ").strip()
                    new_patronimus = input("Отчество: ").strip()
                    contacts = input("Контакты (email/телефон): ").strip()
                    
                    if not new_last_name or not new_first_name:
                        print("Фамилия и имя обязательны для регистрации")
                        return
                        
                    reader_id = self.library.add_reader(new_last_name, new_first_name, new_patronimus, contacts)
                    print(f"Новый читатель зарегистрирован! ID: {reader_id}")
                    reader = {'ID': reader_id, 'LastName': new_last_name, 'FirstName': new_first_name, 'Patronimus': new_patronimus}
                else:
                    print("Выдача книги отменена")
                    return
            
            # Получение дат выдачи
            print(f"\nЧитатель найден: {reader['LastName']} {reader['FirstName']} {reader['Patronimus']}")
            date_of_taking = input("Дата выдачи (ДД.ММ.ГГГГ, сегодня - Enter): ").strip()
            date_of_return = input("Дата возврата (ДД.ММ.ГГГГ, через 14 дней - Enter): ").strip()
            
            # Установка значений по умолчанию
            if not date_of_taking:
                date_of_taking = datetime.now().strftime('%d.%m.%Y')
            
            if not date_of_return:
                # Добавляем 14 дней к текущей дате
                try:
                    return_date = datetime.strptime(date_of_taking, '%d.%m.%Y')
                    return_date = return_date.replace(day=return_date.day + 14)
                    date_of_return = return_date.strftime('%d.%m.%Y')
                except:
                    date_of_return = input("Введите корректную дату возврата (ДД.ММ.ГГГГ): ")
            
            # Выдача книги
            booking_id = self.library.create_booking(
                reader_id=reader['ID'],
                book_id=book_id,
                date_of_taking=date_of_taking,
                date_of_return=date_of_return
            )
            print(f"\nКнига успешно выдана!")
            print(f"ID бронирования: {booking_id}")
            print(f"Дата возврата: {date_of_return}")
            
        except ValueError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
    
    def show_overdue_books(self):
        """Показать просроченные книги"""
        overdue_books = self.library.get_overdue_books()
        print("\n" + "="*50)
        print("ПРОСРОЧЕННЫЕ КНИГИ")
        print("="*50)
        if overdue_books:
            for book in overdue_books:
                print(f"{book['Name']} - Читатель: {book['ReaderName']}, Дата возврата: {book['DateOfReturn']}")
        else:
            print("Нет просроченных книг")
    
    def add_new_book(self):
        """Добавить новую книгу"""
        print("\n" + "="*40)
        print("ДОБАВЛЕНИЕ НОВОЙ КНИГИ")
        print("="*40)
        name = input("Введите название книги: ")
        if name:
            book_id = self.library.add_book(name)
            print(f"Книга добавлена! ID: {book_id}")
        else:
            print("Название книги не может быть пустым")
    
    def add_new_reader(self):
        """Добавить нового читателя"""
        print("\n" + "="*40)
        print("ДОБАВЛЕНИЕ НОВОГО ЧИТАТЕЛЯ")
        print("="*40)
        last_name = input("Фамилия: ")
        first_name = input("Имя: ")
        patronimus = input("Отчество: ")
        contacts = input("Контакты: ")
        
        if last_name and first_name:
            reader_id = self.library.add_reader(last_name, first_name, patronimus, contacts)
            print(f"Читатель добавлен! ID: {reader_id}")
        else:
            print("Фамилия и имя обязательны")
    
    def search_books(self):
        """Поиск книг"""
        print("\n" + "="*40)
        print("ПОИСК КНИГ")
        print("="*40)
        search_term = input("Введите текст для поиска книг: ")
        found_books = self.library.search_books(search_term)
        print(f"\nНайдено книг: {len(found_books)}")
        for book in found_books:
            status = "Выдана" if book['Status'] == 1 else "Доступна"
            print(f"{book['ID']}. {book['Name']} - {status}")
    
    def search_readers(self):
        """Поиск читателей"""
        print("\n" + "="*40)
        print("ПОИСК ЧИТАТЕЛЕЙ")
        print("="*40)
        search_term = input("Введите текст для поиска читателей: ")
        found_readers = self.library.search_readers(search_term)
        print(f"\nНайдено читателей: {len(found_readers)}")
        for reader in found_readers:
            print(f"{reader['ID']}. {reader['LastName']} {reader['FirstName']} {reader['Patronimus']} - {reader['Contacts']}")
    
    def show_menu(self):
        """Показать меню библиотекаря"""
        while True:
            print("\n" + "="*50)
            print("РЕЖИМ БИБЛИОТЕКАРЯ")
            print("="*50)
            print("1. Показать всех читателей")
            print("2. Выдать книгу (поиск читателя по ФИО)")
            print("3. Показать просроченные книги")
            print("4. Добавить новую книгу")
            print("5. Добавить нового читателя")
            print("6. Поиск книг")
            print("7. Поиск читателей")
            print("0. Выйти в главное меню")
            
            choice = input("\nВыберите действие: ")
            
            if choice == "1":
                self.show_all_readers()
            elif choice == "2":
                self.issue_book()
            elif choice == "3":
                self.show_overdue_books()
            elif choice == "4":
                self.add_new_book()
            elif choice == "5":
                self.add_new_reader()
            elif choice == "6":
                self.search_books()
            elif choice == "7":
                self.search_readers()
            elif choice == "0":
                print("Выход из режима библиотекаря...")
                break
            else:
                print("Неверный выбор. Попробуйте еще раз.")


def main_menu():
    """Главное меню для выбора роли"""
    library = LibraryManager()
    
    while True:
        print("\n" + "="*50)
        print("БИБЛИОТЕЧНАЯ СИСТЕМА")
        print("="*50)
        print("1. Режим Читателя")
        print("2. Режим Библиотекаря")
        print("0. Выход")
        
        role_choice = input("\nВыберите роль: ")
        
        if role_choice == "1":
            reader = ReaderInterface(library)
            reader.show_menu()
        elif role_choice == "2":
            librarian = LibrarianInterface(library)
            librarian.show_menu()
        elif role_choice == "0":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте еще раз.")


if __name__ == "__main__":
    main_menu()