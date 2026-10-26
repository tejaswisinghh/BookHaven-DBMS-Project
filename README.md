# 📚 Online Bookstore Management System (BookHaven)

A complete, production-ready, beginner-friendly **Online Bookstore Management System** designed for 2nd-year Relational Database Management System (RDBMS) academic submissions and lab vivas.

Built with **Python (Flask)**, **MySQL Server 8.0**, and a **Modern Vanilla JavaScript SPA Frontend** (HTML5, Modern CSS3).

---

## 🌟 Key Features

- **Relational Integrity:** Implements Primary Keys, Foreign Keys with cascading rules (`ON DELETE CASCADE` and `ON DELETE RESTRICT`), and `CHECK` constraints.
- **ACID Transactions:** Order placement uses atomic database transactions with row-level locking (`SELECT ... FOR UPDATE`) to prevent race conditions and stock overselling.
- **SQL Views:** Includes pre-built reporting views (`CustomerOrderSummary`, `BookSalesSummary`) combining multiple `JOIN`s, `GROUP BY`, and aggregate functions (`COUNT`, `SUM`, `AVG`, `COALESCE`).
- **Full CRUD REST API:** Complete API for Books, Authors, Customers, and Orders.
- **Modern Responsive Dashboard:** Single-Page Application (SPA) with real-time stats, low-stock visual alerts, customer order history, modal dialogs, and instant toast notifications.
- **Zero Heavy Frontend Dependencies:** Runs purely on modern browser APIs (`fetch`, DOM) with no Node.js or React build step required.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Web Browser (SPA)                    │
│    HTML5  •  CSS3 (Modern Design System)  •  Vanilla JS │
└───────────────────────────▲────────────────────────────┘
                            │ JSON REST API
┌───────────────────────────▼────────────────────────────┐
│                  Flask Backend (Python)                │
│    app.py (Routes, Controllers, ACID Transactions)      │
│    db.py (Connection Pool & Context Managers)          │
└───────────────────────────▲────────────────────────────┘
                            │ SQL Queries & Transactions
┌───────────────────────────▼────────────────────────────┐
│                    MySQL Server 8.0                    │
│    Database: BookstoreDB                               │
│    Tables: Authors, Customers, Books, Orders           │
│    Views: CustomerOrderSummary, BookSalesSummary       │
└────────────────────────────────────────────────────────┘
```

---

## 🗄️ Relational Database Schema

### 1. Authors Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `AuthorID` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique author identifier |
| `AuthorName` | VARCHAR(100) | NOT NULL | Full name of the author |
| `Country` | VARCHAR(60) | NOT NULL | Country of origin |
| `CreatedAt` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp of entry |

### 2. Customers Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `CustomerID` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique customer identifier |
| `FullName` | VARCHAR(100) | NOT NULL | Customer name |
| `Email` | VARCHAR(120) | NOT NULL, UNIQUE | Unique email address |
| `Phone` | VARCHAR(20) | NOT NULL | Phone number |
| `City` | VARCHAR(60) | NOT NULL | City of residence |
| `CreatedAt` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration date |

### 3. Books Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `BookID` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique book identifier |
| `Title` | VARCHAR(150) | NOT NULL | Title of the book |
| `AuthorID` | INT | FOREIGN KEY -> Authors(AuthorID) | Linked author |
| `Price` | DECIMAL(10,2)| NOT NULL, CHECK (Price >= 0) | Retail price |
| `StockQuantity`| INT | NOT NULL, CHECK (StockQuantity >= 0)| Inventory stock |
| `CreatedAt` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Addition timestamp |

- **Foreign Key Rule:** `ON DELETE RESTRICT ON UPDATE CASCADE`
  *(Prevents accidental deletion of an author who has books in inventory).*

### 4. Orders Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `OrderID` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique transaction ID |
| `CustomerID` | INT | FOREIGN KEY -> Customers(CustomerID) | Purchasing customer |
| `BookID` | INT | FOREIGN KEY -> Books(BookID) | Purchased book |
| `OrderDate` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date of transaction |
| `QuantityOrdered`| INT | NOT NULL, CHECK (QuantityOrdered > 0)| Units purchased |
| `TotalAmount` | DECIMAL(10,2)| NOT NULL, CHECK (TotalAmount >= 0)| Calculated total |

- **Foreign Key Rules:**
  - `CustomerID`: `ON DELETE CASCADE ON UPDATE CASCADE` *(Deleting a customer removes their historical orders).*
  - `BookID`: `ON DELETE RESTRICT ON UPDATE CASCADE` *(Preserves financial audit records; cannot delete a book with active orders).*

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
1. **Python 3.8+** installed.
2. **MySQL Server 8.0+** running locally on port `3306`.

---

### Step 1: Open the Project Directory
Open your terminal (PowerShell or Command Prompt) and navigate into the project directory:
```powershell
cd "c:\Users\Tejas\OneDrive\Documents\DBMS Project"
```

---

### Step 2: Create a Virtual Environment & Install Dependencies
Create an isolated Python environment and install the required packages:

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate

# 3. Install packages
pip install -r requirements.txt
```

*(Alternatively, install directly without venv: `pip install flask mysql-connector-python python-dotenv PyMySQL cryptography`)*

---

### Step 3: Configure Database Credentials
Edit the `.env` file in the root directory to match your local MySQL Server credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
# Enter your local MySQL root password below. If empty, leave blank:
DB_PASSWORD=your_root_password_here
DB_NAME=BookstoreDB

FLASK_PORT=5000
FLASK_DEBUG=True
```

---

### Step 4: Initialize the Database & Seed Sample Data

You can execute `init_db.sql` using any of the following methods:

#### Option A: Using the Automated Python Script (Recommended)
```powershell
python setup_database.py
```

#### Option B: Using MySQL Command Line
```powershell
mysql -u root -p < init_db.sql
```
*(Enter your MySQL root password when prompted).*

#### Option C: Using MySQL Workbench
1. Open **MySQL Workbench** and connect to your local instance.
2. Click **File -> Open SQL Script...** and select `init_db.sql`.
3. Click the ⚡ **Execute** (lightning bolt) button to run the script.

---

### Step 5: Start the Flask Application
Run the web application server:

```powershell
python app.py
```

You will see output similar to:
```text
============================================================
 📖 Online Bookstore Management System (Flask + MySQL 8.0)
 Server starting at: http://127.0.0.1:5000
 Press CTRL+C to stop.
============================================================
 * Running on http://127.0.0.1:5000
```

---

### Step 6: Open the Web Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Sample Payload |
|---|---|---|---|
| `GET` | `/api/health` | Health check & DB connection status | — |
| `GET` | `/api/books` | Get all books with author details (supports `?q=search`) | — |
| `POST`| `/api/books` | Add a new book | `{"Title": "Clean Code", "AuthorID": 1, "Price": 29.99, "StockQuantity": 10}` |
| `PUT` | `/api/books/<id>` | Update an existing book | `{"Title": "Clean Code", "AuthorID": 1, "Price": 27.99, "StockQuantity": 15}` |
| `DELETE`| `/api/books/<id>` | Delete a book (blocked if orders exist) | — |
| `GET` | `/api/authors` | List all authors | — |
| `POST`| `/api/authors` | Add a new author | `{"AuthorName": "Robert C. Martin", "Country": "United States"}` |
| `GET` | `/api/customers` | Get all customers with order counts | — |
| `POST`| `/api/customers` | Register a new customer | `{"FullName": "John Doe", "Email": "john@example.com", "Phone": "123456", "City": "Boston"}` |
| `DELETE`| `/api/customers/<id>`| Delete customer (cascades to orders) | — |
| `GET` | `/api/orders` | List all orders with Customer & Book joins | — |
| `POST`| `/api/orders` | Place order (ACID check & stock deduction)| `{"CustomerID": 1, "BookID": 2, "QuantityOrdered": 2}` |
| `GET` | `/api/analytics`| Aggregate store metrics & low stock alerts| — |
| `GET` | `/api/reports/customer-summary`| Queries MySQL view `CustomerOrderSummary`| — |

---

## 🎓 Academic Viva & Examiner Q&A Guide

Here are answers to common questions asked during academic DBMS project evaluations:

### Q1: What Normal Form is this database in?
> **Answer:** The schema is normalized up to **3rd Normal Form (3NF)**:
> - **1NF:** Every column contains atomic (indivisible) values and each row is uniquely identified by an integer Primary Key.
> - **2NF:** It is in 1NF and contains no partial dependencies (all non-key attributes are fully functionally dependent on the entire Primary Key).
> - **3NF:** It is in 2NF and contains no transitive dependencies. Author details (AuthorName, Country) are stored in the separate `Authors` table rather than directly in `Books`, eliminating redundancy and update anomalies.

### Q2: How does the application ensure ACID compliance during an order?
> **Answer:**
> 1. **Atomicity & Consistency:** In `app.py` (`place_order`), checking stock, deducting inventory (`UPDATE Books`), and creating the order record (`INSERT INTO Orders`) are performed inside a single database transaction. If any step fails or if stock is insufficient, the transaction rolls back completely with zero side-effects.
> 2. **Isolation:** The query uses `SELECT ... FOR UPDATE` (row-level locking in InnoDB) so concurrent purchase requests do not cause a race condition or sell phantom inventory.
> 3. **Durability:** Changes are permanently saved to MySQL disk logs upon `conn.commit()`.

### Q3: Why is `ON DELETE RESTRICT` used for Books and `ON DELETE CASCADE` for Customers?
> **Answer:**
> - For **Books**: In real-world commerce and accounting, deleting a book that has historical purchase records corrupts financial reporting. `RESTRICT` guarantees audit integrity.
> - For **Customers**: In standard GDPR compliance or customer account closures, deleting a customer profile cascades to their dependent order data (`ON DELETE CASCADE`).

### Q4: What is a View and why is `CustomerOrderSummary` useful?
> **Answer:** A SQL View is a stored query that acts as a virtual table. `CustomerOrderSummary` simplifies complex queries involving `LEFT JOIN`, `GROUP BY`, `COUNT`, `SUM`, and `AVG`. It encapsulates reporting logic in the database engine, improving query reusability and security.

---

## 📁 Project File Structure

```
DBMS Project/
├── init_db.sql              # Database schema, constraints, views & seed data
├── app.py                   # Flask backend REST API & server routes
├── db.py                    # Database connection manager & driver fallback
├── config.py                # Environment configuration loader
├── setup_database.py        # Automated Python setup script
├── requirements.txt         # Python project dependencies
├── .env                     # Local database credentials
├── .env.example             # Configuration template
├── templates/
│   └── index.html           # Modern Single-Page Application (HTML5)
└── static/
    ├── css/
    │   └── style.css        # Responsive styling, design system & toasts
    └── js/
        └── app.js           # Vanilla JS AJAX client & UI controller
```

---

## 👨‍💻 Author & Submission Details
- **Project Title:** Online Bookstore Management System (BookHaven)
- **Course:** Relational Database Management Systems (RDBMS)
- **Academic Year:** 2nd Year B.Tech / B.E. / BCA / MCA
- **Database Engine:** MySQL Server 8.0 (InnoDB Engine)
- **Backend Framework:** Python 3.x with Flask
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (Fetch API)
