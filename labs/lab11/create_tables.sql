CREATE TABLE IF NOT EXISTS PhoneBook (
    Name VARCHAR(100),
    Surname VARCHAR(100),
    Phone VARCHAR(15) UNIQUE,
    CONSTRAINT unique_name_surname UNIQUE(Name, Surname)
);
