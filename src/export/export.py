import sqlite3
import json
import csv
import os
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Optional, List, Dict, Any


class LibraryDB:
    def __init__(self, db_path: str = 'library.db'):
        """
        Инициализация подключения к базе данных
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        
    def get_connection(self):
        """Получение нового соединения с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа к столбцам по имени
        return conn
    
    def get_all_tables(self) -> List[str]:
        """Получение списка всех таблиц в базе данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Получение списка столбцов таблицы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns
    
    def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение всех данных из таблицы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем данные
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Получаем названия столбцов
        columns = [description[0] for description in cursor.description]
        
        # Преобразуем в список словарей
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Преобразуем булевы значения
                if isinstance(value, int) and col.lower() in ['status', 'is_available', 'is_active']:
                    row_dict[col] = bool(value)
                else:
                    row_dict[col] = value
            data.append(row_dict)
        
        conn.close()
        return data
    
    def get_joined_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получение связанных данных из основных таблиц библиотеки
        
        Возвращает словарь с данными:
        - books: книги с информацией о бронировании
        - readers: читатели с информацией о взятых книгах
        - bookings: все бронирования
        - summary: сводная информация
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result = {}
        
        # 1. Книги с информацией о бронировании
        books_query = """
        SELECT 
            b.*,
            bk.id as booking_id,
            bk.reader_id,
            bk.date_taken,
            bk.date_return,
            bk.status as booking_status,
            r.last_name,
            r.first_name,
            r.middle_name,
            r.email,
            r.phone
        FROM books b
        LEFT JOIN bookings bk ON b.id = bk.book_id
        LEFT JOIN readers r ON bk.reader_id = r.id
        ORDER BY b.id
        """
        
        cursor.execute(books_query)
        books_rows = cursor.fetchall()
        books_columns = [description[0] for description in cursor.description]
        
        books_data = []
        for row in books_rows:
            book_dict = {}
            for i, col in enumerate(books_columns):
                book_dict[col] = row[i]
            
            # Структурируем данные о читателе, если они есть
            if book_dict['reader_id']:
                book_dict['reader'] = {
                    'id': book_dict['reader_id'],
                    'last_name': book_dict['last_name'],
                    'first_name': book_dict['first_name'],
                    'middle_name': book_dict['middle_name'],
                    'email': book_dict['email'],
                    'phone': book_dict['phone']
                }
            
            books_data.append(book_dict)
        
        result['books'] = books_data
        
        # 2. Читатели с информацией о взятых книгах
        readers_query = """
        SELECT 
            r.*,
            b.id as book_id,
            b.title,
            b.author,
            b.year,
            b.genre,
            b.isbn,
            bk.date_taken,
            bk.date_return,
            bk.status as booking_status
        FROM readers r
        LEFT JOIN bookings bk ON r.id = bk.reader_id
        LEFT JOIN books b ON bk.book_id = b.id
        ORDER BY r.id
        """
        
        cursor.execute(readers_query)
        readers_rows = cursor.fetchall()
        readers_columns = [description[0] for description in cursor.description]
        
        # Группируем книги по читателям
        readers_dict = {}
        for row in readers_rows:
            reader_id = row[0]  # ID читателя
            
            if reader_id not in readers_dict:
                readers_dict[reader_id] = {
                    'id': reader_id,
                    'last_name': row[1],
                    'first_name': row[2],
                    'middle_name': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'books': []
                }
            
            # Добавляем книгу, если она есть
            if row[6]:  # book_id
                book = {
                    'id': row[6],
                    'title': row[7],
                    'author': row[8],
                    'year': row[9],
                    'genre': row[10],
                    'isbn': row[11],
                    'date_taken': row[12],
                    'date_return': row[13],
                    'booking_status': row[14]
                }
                readers_dict[reader_id]['books'].append(book)
        
        result['readers'] = list(readers_dict.values())
        
        # 3. Все бронирования
        bookings_query = """
        SELECT 
            bk.*,
            b.title,
            b.author,
            r.last_name,
            r.first_name,
            r.middle_name
        FROM bookings bk
        JOIN books b ON bk.book_id = b.id
        JOIN readers r ON bk.reader_id = r.id
        ORDER BY bk.id
        """
        
        cursor.execute(bookings_query)
        bookings_rows = cursor.fetchall()
        bookings_columns = [description[0] for description in cursor.description]
        
        bookings_data = []
        for row in bookings_rows:
            booking_dict = {}
            for i, col in enumerate(bookings_columns):
                booking_dict[col] = row[i]
            bookings_data.append(booking_dict)
        
        result['bookings'] = bookings_data
        
        # 4. Сводная информация
        summary = {
            'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'database_file': self.db_path,
            'tables': self.get_all_tables()
        }
        
        # Получаем статистику
        for table in ['books', 'readers', 'bookings']:
            if table in result:
                summary[f'total_{table}'] = len(result[table])
        
        # Статистика по книгам
        if 'books' in result:
            total_books = len(result['books'])
            available_books = sum(1 for book in result['books'] if not book.get('is_borrowed', False))
            borrowed_books = total_books - available_books
            
            summary['books_statistics'] = {
                'total': total_books,
                'available': available_books,
                'borrowed': borrowed_books,
                'percentage_borrowed': round((borrowed_books / total_books * 100), 2) if total_books > 0 else 0
            }
        
        result['summary'] = summary
        
        conn.close()
        return result


class DataExporter:
    def __init__(self, output_dir: str = 'out'):
        self.output_dir = output_dir
        
        # Создаем папку out, если её нет
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_table_data(self, db: LibraryDB, table_name: str):
        """
        Экспорт данных из конкретной таблицы во все форматы
        
        Args:
            db: Объект базы данных
            table_name: Название таблицы
        """
        print(f"\nЭкспорт таблицы '{table_name}'...")
        
        try:
            # Получаем данные из таблицы
            data = db.get_table_data(table_name)
            
            if not data:
                print(f"  ⚠ Таблица '{table_name}' пуста")
                return
            
            print(f"  ✓ Найдено {len(data)} записей")
            
            # Экспортируем во все форматы
            self.save_to_json(data, table_name)
            self.save_to_csv(data, table_name)
            self.save_to_xml(data, table_name)
            self.save_to_yaml(data, table_name)
            
        except Exception as e:
            print(f"  ✗ Ошибка при экспорте таблицы '{table_name}': {e}")
    
    def export_all_tables(self, db: LibraryDB):
        """
        Экспорт всех таблиц базы данных
        
        Args:
            db: Объект базы данных
        """
        print("\n" + "="*60)
        print("ЭКСПОРТ ВСЕХ ТАБЛИЦ БАЗЫ ДАННЫХ")
        print("="*60)
        
        tables = db.get_all_tables()
        print(f"Найдено таблиц: {len(tables)}")
        
        for table in tables:
            self.export_table_data(db, table)
    
    def export_library_data(self, db: LibraryDB):
        """
        Экспорт структурированных данных библиотеки
        
        Args:
            db: Объект базы данных
        """
        print("\n" + "="*60)
        print("ЭКСПОРТ СТРУКТУРИРОВАННЫХ ДАННЫХ БИБЛИОТЕКИ")
        print("="*60)
        
        try:
            # Получаем структурированные данные
            data = db.get_joined_data()
            
            # Экспортируем каждую категорию данных
            for category, category_data in data.items():
                print(f"\nЭкспорт '{category}'...")
                
                if isinstance(category_data, list):
                    print(f"  ✓ Найдено {len(category_data)} записей")
                    self.export_data(category_data, category)
                elif isinstance(category_data, dict):
                    print(f"  ✓ Экспорт словаря")
                    self.export_data([category_data], category)
            
            # Создаем объединенный файл со всеми данными
            self.save_to_json(data, 'library_full_data')
            
            print("\n" + "="*60)
            print("ЭКСПОРТ ЗАВЕРШЕН УСПЕШНО!")
            print("="*60)
            
        except Exception as e:
            print(f"\n✗ Ошибка при экспорте структурированных данных: {e}")
    
    def export_data(self, data: List[Dict[str, Any]], filename: str):
        """
        Экспорт данных во все форматы: JSON, CSV, XML, YAML
        
        Args:
            data: Данные для экспорта
            filename: Базовое имя для файлов
        """
        self.save_to_json(data, filename)
        self.save_to_csv(data, filename)
        self.save_to_xml(data, filename)
        self.save_to_yaml(data, filename)
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Сохранение данных в JSON"""
        filepath = os.path.join(self.output_dir, f'{filename}.json')
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print(f"  ✓ JSON сохранен: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Ошибка при сохранении JSON: {e}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Сохранение данных в CSV (плоский формат)"""
        filepath = os.path.join(self.output_dir, f'{filename}.csv')
        
        if not data:
            return
        
        try:
            # Преобразуем вложенные структуры в плоские
            flat_data = []
            for item in data:
                flat_item = self._flatten_dict(item)
                flat_data.append(flat_item)
            
            # Записываем в CSV
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                fieldnames = list(flat_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flat_data)
            
            print(f"  ✓ CSV сохранен: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Ошибка при сохранении CSV: {e}")
    
    def save_to_xml(self, data: List[Dict[str, Any]], filename: str):
        """Сохранение данных в XML"""
        filepath = os.path.join(self.output_dir, f'{filename}.xml')
        
        try:
            # Создаем корневой элемент
            root_name = filename if not filename.endswith('s') else filename[:-1]
            root = ET.Element(f'{root_name}s')
            
            for item in data:
                item_elem = ET.SubElement(root, root_name)
                self._dict_to_xml(item_elem, item)
            
            # Форматируем и сохраняем XML
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            
            print(f"  ✓ XML сохранен: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Ошибка при сохранении XML: {e}")
    
    def save_to_yaml(self, data: List[Dict[str, Any]], filename: str):
        """Сохранение данных в YAML"""
        filepath = os.path.join(self.output_dir, f'{filename}.yaml')
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"  ✓ YAML сохранен: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Ошибка при сохранении YAML: {e}")
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Преобразование вложенного словаря в плоский"""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep))
            elif isinstance(v, list):
                # Для списков сохраняем как JSON строку
                items[new_key] = json.dumps(v, ensure_ascii=False, default=str)
            elif isinstance(v, bool):
                items[new_key] = 'true' if v else 'false'
            elif v is None:
                items[new_key] = ''
            else:
                items[new_key] = str(v)
        
        return items
    
    def _dict_to_xml(self, parent: ET.Element, data: Dict[str, Any]):
        """Рекурсивное преобразование словаря в XML"""
        for key, value in data.items():
            if isinstance(value, dict):
                child = ET.SubElement(parent, key.replace(' ', '_'))
                self._dict_to_xml(child, value)
            elif isinstance(value, list):
                list_elem = ET.SubElement(parent, key.replace(' ', '_'))
                for item in value:
                    if isinstance(item, dict):
                        item_elem = ET.SubElement(list_elem, 'item')
                        self._dict_to_xml(item_elem, item)
                    else:
                        ET.SubElement(list_elem, 'item').text = str(item)
            else:
                elem = ET.SubElement(parent, key.replace(' ', '_'))
                if isinstance(value, bool):
                    elem.text = 'true' if value else 'false'
                elif value is not None:
                    elem.text = str(value)


def print_file_sizes(output_dir: str = 'out'):
    """Вывод информации о созданных файлах"""
    if not os.path.exists(output_dir):
        print(f"\nПапка '{output_dir}' не существует")
        return
    
    print("\n" + "="*60)
    print("СОЗДАННЫЕ ФАЙЛЫ:")
    print("="*60)
    
    files = os.listdir(output_dir)
    total_size = 0
    
    for file in sorted(files):
        filepath = os.path.join(output_dir, file)
        size = os.path.getsize(filepath)
        total_size += size
        
        # Определяем тип файла
        if file.endswith('.json'):
            file_type = 'JSON'
        elif file.endswith('.csv'):
            file_type = 'CSV'
        elif file.endswith('.xml'):
            file_type = 'XML'
        elif file.endswith('.yaml') or file.endswith('.yml'):
            file_type = 'YAML'
        else:
            file_type = 'Другой'
        
        print(f"  {file_type:6} {file:30} {size:10} байт")
    
    print("-" * 60)
    print(f"  Всего файлов: {len(files):10}")
    print(f"  Общий размер: {total_size:10} байт")


def interactive_menu():
    """Интерактивное меню для работы с экспортом данных"""
    db_path = 'library.db'
    
    if not os.path.exists(db_path):
        print(f"\n⚠ Файл базы данных '{db_path}' не найден!")
        print("Убедитесь, что файл находится в той же папке, что и скрипт.")
        return
    
    db = LibraryDB(db_path)
    exporter = DataExporter()
    
    while True:
        print("\n" + "="*60)
        print("СИСТЕМА ЭКСПОРТА ДАННЫХ БИБЛИОТЕКИ")
        print("="*60)
        print(f"База данных: {db_path}")
        
        tables = db.get_all_tables()
        print(f"Таблиц в базе: {len(tables)}")
        
        print("\nДоступные действия:")
        print("1. Показать все таблицы")
        print("2. Экспортировать все таблицы (каждую в отдельные файлы)")
        print("3. Экспортировать структурированные данные библиотеки")
        print("4. Экспортировать конкретную таблицу")
        print("5. Показать созданные файлы")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            print("\nТаблицы в базе данных:")
            for i, table in enumerate(tables, 1):
                columns = db.get_table_columns(table)
                print(f"{i:2}. {table:20} ({len(columns)} колонок)")
                if len(columns) <= 10:
                    print(f"     Колонки: {', '.join(columns)}")
                else:
                    print(f"     Колонки: {', '.join(columns[:5])}... и еще {len(columns)-5}")
        
        elif choice == "2":
            print("\nЭкспорт всех таблиц...")
            exporter.export_all_tables(db)
            print_file_sizes()
        
        elif choice == "3":
            print("\nЭкспорт структурированных данных библиотеки...")
            exporter.export_library_data(db)
            print_file_sizes()
        
        elif choice == "4":
            if not tables:
                print("\nВ базе данных нет таблиц")
                continue
            
            print("\nДоступные таблицы:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table}")
            
            try:
                table_num = int(input("\nВыберите номер таблицы: "))
                if 1 <= table_num <= len(tables):
                    table_name = tables[table_num - 1]
                    exporter.export_table_data(db, table_name)
                    print_file_sizes()
                else:
                    print("Неверный номер таблицы")
            except ValueError:
                print("Пожалуйста, введите число")
        
        elif choice == "5":
            print_file_sizes()

# Основная функция
def main():
    """Основная функция программы"""
    print("="*60)
    print("СИСТЕМА ЭКСПОРТА ДАННЫХ БИБЛИОТЕКИ")
    print("="*60)
    
    # Проверяем наличие базы данных
    db_path = 'library.db'
    if not os.path.exists(db_path):
        print(f"⚠ ВНИМАНИЕ: Файл базы данных '{db_path}' не найден!")
        print("Пожалуйста, поместите файл library.db в ту же папку, что и скрипт.")
        
        # Спрашиваем, хочет ли пользователь продолжить
        choice = input("\nПродолжить без базы данных? (y/n): ").lower()
        if choice != 'y':
            print("Завершение работы программы...")
            return
    
    while True:
        print("\nВыберите режим работы:")
        print("1. Интерактивное меню")
        print("0. Выход")
        
        choice = input("\nВыберите режим: ").strip()
        
        if choice == "1":
            interactive_menu()

        elif choice == "0":
            print("\nЗавершение работы программы...")
            break
        else:
            print("Неверный выбор. Попробуйте еще раз.")


if __name__ == "__main__":
    main()