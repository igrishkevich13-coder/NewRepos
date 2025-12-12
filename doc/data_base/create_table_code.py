import sqlite3

conn = sqlite3.connect('library.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Books (
    ID INTEGER PRIMARY KEY,
    Booking_ID INTEGER,
    Name TEXT NOT NULL,
    Status TEXT,
    FOREIGN KEY(Booking_ID) REFERENCES Booking(ID)
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Readers (
    ID INTEGER PRIMARY KEY,
    LastName TEXT NOT NULL,
    FirstName TEXT NOT NULL,
    Patronimus TEXT NOT NULL,
    contacts TEXT NOT NULL
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Booking (
    ID INTEGER PRIMARY KEY,
    Reader_ID INTEGER NOT NULL,
    data_of_taking TEXT NOT NULL,
    data_of_giving_back TEXT NOT NULL,
    FOREIGN KEY(Reader_ID) REFERENCES Readers(ID)
);
''')

#cursor.execute("INSERT INTO Readers (LastName, FirstName, Patronimus, contacts) VALUES ('Иваненко','Иван','Иванович','mail1@mail.ru')")
#cursor.execute("INSERT INTO Readers (LastName, FirstName, Patronimus, contacts) VALUES ('Иваненко','Анна','Ивановна','mail2@mail.ru')")
#cursor.execute("INSERT INTO Readers (LastName, FirstName, Patronimus, contacts) VALUES ('Петров','Пётр','Петрович','mail3@mail.ru')")
#cursor.execute("INSERT INTO Readers (LastName, FirstName, Patronimus, contacts) VALUES ('Николаев','Николай','Николаевич','mail4@mail.ru')")
#cursor.execute("INSERT INTO Readers (LastName, FirstName, Patronimus, contacts) VALUES ('Васильев','Василий','Васильевич','mail5@mail.ru')")

#cursor.execute("INSERT INTO Books (Name, Booking_ID) VALUES ('Война и мир', 1)")
#cursor.execute("INSERT INTO Books (Name, Booking_ID) VALUES ('Мёртвые души', 2)")
#cursor.execute("INSERT INTO Books (Name, Booking_ID) VALUES ('Гроза', 3)")
#cursor.execute("INSERT INTO Books (Name, Booking_ID) VALUES ('Недоросль', 4)")
#cursor.execute("INSERT INTO Books (Name, Booking_ID) VALUES ('Горе от ума', 5)")
#cursor.execute("INSERT INTO Books (Name) VALUES ('Евгений Онегин')")
#cursor.execute("INSERT INTO Books (Name) VALUES ('Герой нашего времени')")
#cursor.execute("INSERT INTO Books (Name) VALUES ('Отцы и дети')")
#cursor.execute("INSERT INTO Books (Name) VALUES ('Преступление и наказание')")
#cursor.execute("INSERT INTO Books (Name) VALUES ('Тихий Дон')")

cursor.execute("INSERT INTO Booking (Reader_ID, data_of_taking, data_of_giving_back) VALUES (1,'01.12.2025','14.12.2025')")
cursor.execute("INSERT INTO Booking (Reader_ID, data_of_taking, data_of_giving_back) VALUES (2,'01.12.2025','14.12.2025')")
cursor.execute("INSERT INTO Booking (Reader_ID, data_of_taking, data_of_giving_back) VALUES (3,'01.12.2025','14.12.2025')")
cursor.execute("INSERT INTO Booking (Reader_ID, data_of_taking, data_of_giving_back) VALUES (4,'01.12.2025','14.12.2025')")
cursor.execute("INSERT INTO Booking (Reader_ID, data_of_taking, data_of_giving_back) VALUES (5,'01.12.2025','14.12.2025')")

cursor.execute("SELECT * FROM Books")
cursor.execute("SELECT * FROM Readers")
cursor.execute("SELECT * FROM Booking")

conn.commit()
conn.close()