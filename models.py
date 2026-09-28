"""
models.py
----------
This file defines all the database tables for the Restaurant Management
System using SQLAlchemy ORM. Each Python class below becomes one table
in the SQLite database (database.db).

Beginner note:
    SQLAlchemy lets us work with database rows as if they were normal
    Python objects, instead of writing raw SQL everywhere.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This "db" object is created here and imported into app.py.
# It is the main connector between Flask and SQLite.
db = SQLAlchemy()


class MenuItem(db.Model):
    """Represents one dish/item available on the restaurant menu."""
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # available stock of this dish

    # One menu item can appear in many order items
    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity,
        }


class RestaurantTable(db.Model):
    """Represents one physical table in the restaurant."""
    __tablename__ = "restaurant_tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)
    # status can be: 'Available', 'Reserved', 'Occupied'
    status = db.Column(db.String(20), nullable=False, default="Available")

    reservations = db.relationship("Reservation", backref="table", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "table_number": self.table_number,
            "capacity": self.capacity,
            "status": self.status,
        }


class Reservation(db.Model):
    """Represents a customer's table reservation."""
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)   # stored as YYYY-MM-DD
    time = db.Column(db.String(10), nullable=False)   # stored as HH:MM
    guests = db.Column(db.Integer, nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey("restaurant_tables.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "date": self.date,
            "time": self.time,
            "guests": self.guests,
            "table_id": self.table_id,
        }


class Order(db.Model):
    """Represents one customer order (a basket of menu items)."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    # status can be: 'Pending', 'Completed', 'Cancelled'
    status = db.Column(db.String(20), nullable=False, default="Completed")

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_date": self.order_date.strftime("%Y-%m-%d %H:%M"),
            "total_amount": self.total_amount,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    """Represents a single menu item line inside an order."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "menu_item_id": self.menu_item_id,
            "menu_item_name": self.menu_item.name if self.menu_item else None,
            "quantity": self.quantity,
            "subtotal": self.subtotal,
        }


class Inventory(db.Model):
    """Represents one raw ingredient kept in stock."""
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)  # e.g. kg, litres, pieces
    unit = db.Column(db.String(20), nullable=False, default="units")
    low_stock_threshold = db.Column(db.Float, nullable=False, default=5)

    def to_dict(self):
        return {
            "id": self.id,
            "ingredient_name": self.ingredient_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low": self.quantity <= self.low_stock_threshold,
        }
