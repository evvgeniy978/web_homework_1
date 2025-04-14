from collections import UserDict
from datetime import datetime, timedelta
import pickle
from abc import ABC, abstractmethod

# Абстракція для серіалізації (D)
class Storage(ABC):
    @abstractmethod
    def save(self, book, filename):
        pass

    @abstractmethod
    def load(self, filename):
        pass

class PickleStorage(Storage):
    def save(self, book, filename="addressbook.pkl"):
        with open(filename, "wb") as f:
            pickle.dump(book, f)

    def load(self, filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return AddressBook()

# Клас для обробки полів
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для імені
class Name(Field):
    pass

# Клас для номера телефону з валідацією
class Phone(Field):
    def __init__(self, value):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be a string of 10 digits")
        super().__init__(value)

# Клас для дати народження з валідацією формату DD.MM.YYYY
class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Інтерфейс для управління телефонами (I)
class PhoneManager:
    def __init__(self):
        self.phones = []

    def add_phone(self, phone):
        new_phone = Phone(phone)
        self.phones.append(new_phone)

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        Phone(new_phone)
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                break
        else:
            raise ValueError(f"Phone {old_phone} not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def get_phones_str(self):
        return ", ".join(p.value for p in self.phones) if self.phones else "No phones"

# Інтерфейс для управління днями народження (I)
class BirthdayManager:
    def __init__(self):
        self.birthday = None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def get_birthday_str(self):
        return f", birthday: {self.birthday}" if self.birthday else ""

# Клас для запису контакту (S, O, I)
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phone_manager = PhoneManager()
        self.birthday_manager = BirthdayManager()

    def __str__(self):
        return f"Contact name: {self.name}, phones: {self.phone_manager.get_phones_str()}{self.birthday_manager.get_birthday_str()}"

# Клас для обчислення найближчих днів народження (S)
class BirthdayCalculator:
    def get_upcoming_birthdays(self, records, today=None):
        if today is None:
            today = datetime.today()
        upcoming = []
        for record in records:
            if record.birthday_manager.birthday:
                bday = datetime.strptime(record.birthday_manager.birthday.value, "%d.%m.%Y")
                bday_this_year = bday.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                delta = (bday_this_year - today).days
                if 0 <= delta <= 7:
                    congratulation_date = bday_this_year
                    weekday = congratulation_date.weekday()
                    if weekday == 5:
                        congratulation_date += timedelta(days=2)
                    elif weekday == 6:
                        congratulation_date += timedelta(days=1)
                    upcoming.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                    })
        return upcoming

# Інтерфейс для роботи з адресною книгою (I)
class AddressBookInterface(ABC):
    @abstractmethod
    def add_record(self, record):
        pass

    @abstractmethod
    def find(self, name):
        pass

# Клас для адресної книги
class AddressBook(UserDict, AddressBookInterface):
    def add_record(self, record):
        self.data[record.name.value] = record

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def find(self, name):
        return self.data.get(name)

    def get_all_records(self):
        return list(self.data.values())

# Патерн "Команда" для обробки команд (O)
class Command(ABC):
    @abstractmethod
    def execute(self, args, book):
        pass

class AddContactCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if len(args) != 2:
            raise ValueError("Command 'add' requires 2 arguments: name and phone")
        name, phone = args
        record = book.find(name)
        message = "Contact added."
        if record is None:
            record = Record(name)
            book.add_record(record)
        record.phone_manager.add_phone(phone)
        return message

class ChangeContactCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if len(args) != 3:
            raise ValueError("Command 'change' requires 3 arguments: name, old_phone, new_phone")
        name, old_phone, new_phone = args
        record = book.find(name)
        if record is None:
            return "Contact not found."
        record.phone_manager.edit_phone(old_phone, new_phone)
        return "Phone number updated."

class ShowPhoneCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if len(args) != 1:
            raise ValueError("Command 'phone' requires 1 argument: name")
        name, = args
        record = book.find(name)
        if record is None:
            return "Contact not found."
        return str(record)

class ShowAllCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if not book.data:
            return "No contacts found."
        return "\n".join(str(record) for record in book.data.values())

class AddBirthdayCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if len(args) != 2:
            raise ValueError("Command 'add-birthday' requires 2 arguments: name and birthday")
        name, birthday = args
        record = book.find(name)
        if record is None:
            return "Contact not found."
        record.birthday_manager.add_birthday(birthday)
        return "Birthday added."

class ShowBirthdayCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        if len(args) != 1:
            raise ValueError("Command 'show-birthday' requires 1 argument: name")
        name, = args
        record = book.find(name)
        if record is None:
            return "Contact not found."
        if record.birthday_manager.birthday is None:
            return "Birthday not set."
        return f"{record.name}'s birthday: {record.birthday_manager.birthday}"

class BirthdaysCommand(Command):
    def execute(self, args, book: AddressBookInterface):
        calculator = BirthdayCalculator()
        upcoming = calculator.get_upcoming_birthdays(book.get_all_records())
        if not upcoming:
            return "No upcoming birthdays in the next 7 days."
        return "\n".join(f"{entry['name']}: {entry['congratulation_date']}" for entry in upcoming)

# Декоратор для обробки помилок (S)
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, KeyError, IndexError) as e:
            return f"Error: {str(e)}"
    return inner

# Декоратор для збереження даних (S)
def save_on_change(storage: Storage):
    def decorator(func):
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            book = args[1]  # Другий аргумент - це book
            storage.save(book)
            return result
        return inner
    return decorator

# Функція для парсингу введення користувача
def parse_input(user_input):
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.strip().lower().split()
    return cmd, args

# Головна функція
def main():
    storage = PickleStorage()
    book = storage.load()
    command_map = {
        "add": AddContactCommand(),
        "change": ChangeContactCommand(),
        "phone": ShowPhoneCommand(),
        "all": ShowAllCommand(),
        "add-birthday": AddBirthdayCommand(),
        "show-birthday": ShowBirthdayCommand(),
        "birthdays": BirthdaysCommand(),
    }

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            storage.save(book)
            break
        elif command == "":
            print("Please enter a command.")
        elif command == "hello":
            print("How can I help you?")
        elif command in command_map:
            cmd = command_map[command]
            decorated_cmd = save_on_change(storage)(input_error(cmd.execute))
            print(decorated_cmd(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()