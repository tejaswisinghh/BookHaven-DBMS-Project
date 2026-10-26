-- =====================================================================
-- Online Bookstore Management System (BookstoreDB)
-- 2nd-Year RDBMS Academic Project Database Script
-- Compatible with MySQL Server 8.0+
-- =====================================================================

-- Step 1: Initialize Database
DROP DATABASE IF EXISTS BookstoreDB;
CREATE DATABASE BookstoreDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE BookstoreDB;

-- Step 2: Create Table: Authors
-- Stores information about book authors.
CREATE TABLE Authors (
    AuthorID INT AUTO_INCREMENT PRIMARY KEY,
    AuthorName VARCHAR(100) NOT NULL,
    Country VARCHAR(60) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Step 3: Create Table: Customers
-- Stores customer profiles with unique email constraint.
CREATE TABLE Customers (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    Email VARCHAR(120) NOT NULL UNIQUE,
    Phone VARCHAR(20) NOT NULL,
    City VARCHAR(60) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Step 4: Create Table: Books
-- Stores book details, linked to Authors with Foreign Key and cascading rules.
-- CHECK constraints ensure valid prices and non-negative stock counts.
CREATE TABLE Books (
    BookID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(150) NOT NULL,
    AuthorID INT NOT NULL,
    Price DECIMAL(10, 2) NOT NULL,
    StockQuantity INT NOT NULL DEFAULT 0,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_book_price CHECK (Price >= 0.00),
    CONSTRAINT chk_book_stock CHECK (StockQuantity >= 0),
    CONSTRAINT fk_books_author FOREIGN KEY (AuthorID) 
        REFERENCES Authors (AuthorID) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Step 5: Create Table: Orders
-- Records purchase transactions, linking Customers and Books.
-- Cascading rules: Deleting a customer cascades to their orders;
-- Deleting a book with existing orders is restricted to preserve financial history.
CREATE TABLE Orders (
    OrderID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    BookID INT NOT NULL,
    OrderDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    QuantityOrdered INT NOT NULL,
    TotalAmount DECIMAL(10, 2) NOT NULL,
    CONSTRAINT chk_order_qty CHECK (QuantityOrdered > 0),
    CONSTRAINT chk_order_total CHECK (TotalAmount >= 0.00),
    CONSTRAINT fk_orders_customer FOREIGN KEY (CustomerID) 
        REFERENCES Customers (CustomerID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_orders_book FOREIGN KEY (BookID) 
        REFERENCES Books (BookID) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Step 6: Create Indexes for Query Optimization
CREATE INDEX idx_books_author ON Books(AuthorID);
CREATE INDEX idx_orders_customer ON Orders(CustomerID);
CREATE INDEX idx_orders_book ON Orders(BookID);
CREATE INDEX idx_orders_date ON Orders(OrderDate);

-- =====================================================================
-- Step 7: Views for Academic Viva & Reporting
-- =====================================================================

-- View 1: Customer Order Summary
-- Demonstrates LEFT JOIN, GROUP BY, and Aggregate functions (COUNT, SUM, AVG, COALESCE)
CREATE OR REPLACE VIEW CustomerOrderSummary AS
SELECT 
    c.CustomerID,
    c.FullName,
    c.Email,
    c.City,
    COUNT(o.OrderID) AS TotalOrders,
    COALESCE(SUM(o.QuantityOrdered), 0) AS TotalBooksPurchased,
    COALESCE(SUM(o.TotalAmount), 0.00) AS TotalSpent,
    COALESCE(ROUND(AVG(o.TotalAmount), 2), 0.00) AS AverageOrderValue
FROM Customers c
LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.FullName, c.Email, c.City;

-- View 2: Book Sales & Inventory Summary
-- Demonstrates JOIN, Aggregate reporting, and Stock status
CREATE OR REPLACE VIEW BookSalesSummary AS
SELECT 
    b.BookID,
    b.Title,
    a.AuthorName,
    b.Price,
    b.StockQuantity,
    COALESCE(SUM(o.QuantityOrdered), 0) AS CopiesSold,
    COALESCE(SUM(o.TotalAmount), 0.00) AS TotalRevenueGenerated,
    CASE 
        WHEN b.StockQuantity = 0 THEN 'Out of Stock'
        WHEN b.StockQuantity < 5 THEN 'Low Stock'
        ELSE 'In Stock'
    END AS StockStatus
FROM Books b
JOIN Authors a ON b.AuthorID = a.AuthorID
LEFT JOIN Orders o ON b.BookID = o.BookID
GROUP BY b.BookID, b.Title, a.AuthorName, b.Price, b.StockQuantity;

-- =====================================================================
-- Step 8: Seed Sample Data
-- =====================================================================

-- Insert Authors (6 records)
INSERT INTO Authors (AuthorID, AuthorName, Country) VALUES
(1, 'J.K. Rowling', 'United Kingdom'),
(2, 'George Orwell', 'United Kingdom'),
(3, 'F. Scott Fitzgerald', 'United States'),
(4, 'Harper Lee', 'United States'),
(5, 'Yuval Noah Harari', 'Israel'),
(6, 'Agatha Christie', 'United Kingdom');

-- Insert Customers (6 records)
INSERT INTO Customers (CustomerID, FullName, Email, Phone, City) VALUES
(1, 'Alice Johnson', 'alice.j@example.com', '+1-555-0101', 'New York'),
(2, 'Rahul Sharma', 'rahul.s@example.com', '+91-98765-43210', 'Mumbai'),
(3, 'Elena Rostova', 'elena.r@example.com', '+44-20-7946-0912', 'London'),
(4, 'David Chen', 'david.chen@example.com', '+1-555-0145', 'San Francisco'),
(5, 'Priya Patel', 'priya.patel@example.com', '+91-98111-22334', 'Bengaluru'),
(6, 'Carlos Mendes', 'carlos.m@example.com', '+34-91-123-4567', 'Madrid');

-- Insert Books (8 records across various genres, prices, and stock)
INSERT INTO Books (BookID, Title, AuthorID, Price, StockQuantity) VALUES
(1, 'Harry Potter and the Sorcerer''s Stone', 1, 19.99, 25),
(2, '1984', 2, 14.50, 18),
(3, 'Animal Farm', 2, 9.99, 4),               -- Low stock example
(4, 'The Great Gatsby', 3, 12.75, 12),
(5, 'To Kill a Mockingbird', 4, 15.20, 8),
(6, 'Sapiens: A Brief History of Humankind', 5, 24.99, 15),
(7, 'And Then There Were None', 6, 11.50, 3),   -- Low stock example
(8, 'Murder on the Orient Express', 6, 13.99, 0); -- Out of stock example

-- Insert Orders (8 realistic historical orders)
INSERT INTO Orders (OrderID, CustomerID, BookID, OrderDate, QuantityOrdered, TotalAmount) VALUES
(1, 1, 1, '2026-10-10 10:15:00', 2, 39.98),
(2, 2, 6, '2026-10-12 14:30:00', 1, 24.99),
(3, 3, 2, '2026-10-14 11:20:00', 1, 14.50),
(4, 4, 4, '2026-10-15 16:45:00', 2, 25.50),
(5, 5, 5, '2026-10-18 09:10:00', 1, 15.20),
(6, 1, 3, '2026-10-19 13:05:00', 1, 9.99),
(7, 2, 1, '2026-10-21 17:50:00', 1, 19.99),
(8, 6, 7, '2026-10-23 12:40:00', 2, 23.00);

-- Reset AUTO_INCREMENT counters to continue seamlessly after seed data
ALTER TABLE Authors AUTO_INCREMENT = 7;
ALTER TABLE Customers AUTO_INCREMENT = 7;
ALTER TABLE Books AUTO_INCREMENT = 9;
ALTER TABLE Orders AUTO_INCREMENT = 9;

-- =====================================================================
-- Verification & Academic Viva Demonstration Queries
-- =====================================================================

-- 1. Verify all books with Author Details (INNER JOIN)
-- SELECT b.BookID, b.Title, a.AuthorName, a.Country, b.Price, b.StockQuantity
-- FROM Books b
-- INNER JOIN Authors a ON b.AuthorID = a.AuthorID;

-- 2. Verify all orders with Customer & Book details (Multiple JOINS)
-- SELECT o.OrderID, o.OrderDate, c.FullName, b.Title, o.QuantityOrdered, o.TotalAmount
-- FROM Orders o
-- JOIN Customers c ON o.CustomerID = c.CustomerID
-- JOIN Books b ON o.BookID = b.BookID
-- ORDER BY o.OrderDate DESC;

-- 3. Top selling books by total units ordered (Aggregation + GROUP BY + ORDER BY)
-- SELECT b.Title, SUM(o.QuantityOrdered) AS UnitsSold, SUM(o.TotalAmount) AS Revenue
-- FROM Orders o
-- JOIN Books b ON o.BookID = b.BookID
-- GROUP BY b.BookID, b.Title
-- ORDER BY UnitsSold DESC;

-- 4. Check View Output
-- SELECT * FROM CustomerOrderSummary;
-- SELECT * FROM BookSalesSummary;
