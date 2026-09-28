# 🍽️ CodeAlpha_RestaurantManagement

A complete **Restaurant Management System** built with **Flask** and **SQLite**, created for the **CodeAlpha Backend Development Internship — Task 3**.

This project provides a full backend (with a polished dark-themed UI) for managing a restaurant's menu, tables, reservations, orders, and inventory — plus an admin dashboard with live statistics.

---

## 📖 Project Overview

Restaurants need a simple, reliable system to manage day-to-day operations: what's on the menu, which tables are free, who has reserved a table, what customers have ordered, and how much stock is left. **CodeAlpha_RestaurantManagement** solves this with a Flask backend, a normalized SQLite schema, and clean CRUD routes for every module — wrapped in a professional, responsive, dark "premium restaurant" UI.

---

## ✨ Features

### 1. Menu Management
- Add, edit, delete, and view menu items
- Fields: item name, category, price, available quantity
- Out-of-stock items are automatically flagged

### 2. Table Management
- Add tables with number and capacity
- Update table status: `Available`, `Reserved`, `Occupied`

### 3. Reservation System
- Customers can reserve a table (name, phone, date, time, guests)
- **Prevents double booking**: the same table cannot be reserved twice for the same date and time
- Automatically marks the reserved table's status as `Reserved`

### 4. Order Management
- Customers select menu items and quantities
- Total amount is calculated automatically
- Orders and order line items are saved to the database
- Menu stock is reduced automatically per order

### 5. Inventory Management
- Add ingredients and track stock levels
- Update stock manually at any time
- **Stock automatically decreases** when a matching menu item is ordered
- Low-stock ingredients are flagged automatically

### 6. Admin Dashboard
- Total Orders
- Total Revenue
- Total Reservations
- Available Tables
- Low Stock Alerts
- Recent Orders feed

---

## 🛠️ Tech Stack

**Backend:** Flask (Python), SQLAlchemy ORM, SQLite
**Frontend:** HTML5, CSS3 (custom dark "premium restaurant" theme), Vanilla JavaScript

---

## 📁 Folder Structure

```
CodeAlpha_RestaurantManagement/
│
├── app.py                  # Main Flask application & all routes
├── models.py                # SQLAlchemy database models
├── database.db               # SQLite database (auto-created on first run)
├── requirements.txt          # Python dependencies
├── README.md
│
├── templates/
│   ├── base.html              # Shared layout (navbar, footer, flash messages)
│   ├── index.html             # Home page
│   ├── dashboard.html         # Admin dashboard
│   ├── menu.html              # Menu list
│   ├── add_menu.html          # Add / edit menu item form
│   ├── tables.html            # Table list + status update
│   ├── add_table.html         # Add table form
│   ├── reservations.html      # Reservation list
│   ├── reserve.html           # Reservation form
│   ├── order_create.html      # Place new order (live total)
│   ├── order_history.html     # Past orders
│   ├── inventory.html         # Inventory list + stock update
│   └── add_inventory.html     # Add ingredient form
│
├── static/
│   ├── style.css              # Premium dark restaurant theme
│   └── script.js              # Nav toggle, live order total, flash auto-dismiss
│
└── screenshots/               # Add your UI screenshots here
```

---

## 🗄️ Database Schema

| Table              | Fields |
|---------------------|--------|
| **MenuItems**        | id, name, category, price, quantity |
| **RestaurantTables** | id, table_number, capacity, status |
| **Reservations**     | id, customer_name, phone, date, time, guests, table_id |
| **Orders**           | id, order_date, total_amount, status |
| **OrderItems**       | id, order_id, menu_item_id, quantity, subtotal |
| **Inventory**        | id, ingredient_name, quantity |

The database (`database.db`) and all tables are created automatically the first time you run the app, along with a few sample rows so the UI isn't empty on first launch.

---

## 🚀 Installation Steps

1. **Clone or download this project**
   ```bash
   git clone https://github.com/<your-username>/CodeAlpha_RestaurantManagement.git
   cd CodeAlpha_RestaurantManagement
   ```

2. **(Recommended) Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in your browser**
   ```
   http://127.0.0.1:5000
   ```

That's it — the SQLite database and sample data are created automatically on first run.

---

## 🧭 Routes Reference

| Route | Description |
|---|---|
| `/` | Home page |
| `/menu` | View menu |
| `/menu/add` | Add menu item |
| `/menu/edit/<id>` | Edit menu item |
| `/menu/delete/<id>` | Delete menu item |
| `/tables` | View tables |
| `/tables/add` | Add table |
| `/reservations` | View reservations |
| `/reserve` | Reserve a table |
| `/orders` | Redirects to order history |
| `/order/create` | Place a new order |
| `/order/history` | View past orders |
| `/inventory` | View inventory |
| `/inventory/add` | Add ingredient |
| `/dashboard` | Admin dashboard |

---

## 📸 Screenshots

_Add screenshots of your running app to the `screenshots/` folder and reference them here, e.g.:_

```markdown
![Dashboard](screenshots/dashboard.png)
![Menu Management](screenshots/menu.png)
```

---

## 🔮 Future Enhancements

- User authentication (Admin vs Customer roles)
- Online payment integration
- Email/SMS confirmation for reservations
- Printable/exportable order receipts (PDF)
- REST API endpoints (JSON) for a future mobile app
- Real-time table status updates with WebSockets
- Analytics charts on the dashboard (revenue trends, best-selling items)

---

## 👤 Author

Built as part of the **CodeAlpha Backend Development Internship — Task 3**.
