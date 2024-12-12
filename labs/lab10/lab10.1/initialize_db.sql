CREATE TABLE IF NOT EXISTS PhoneBook (
    Name VARCHAR(50),
    Surname VARCHAR(50),
    Phone VARCHAR(15),
    PRIMARY KEY (Name, Surname, Phone)
);
