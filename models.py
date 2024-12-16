#all imports
from app import db
from flask import session 
from flask_login import UserMixin,current_user
from werkzeug.security import generate_password_hash

#setting up cart items and adding keys for db linking 
cart_items = db.Table('cart_items',db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True))

#user class with attribtues and hashing their password so its not accesible to us
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    cart_items = db.relationship('Cart', back_populates='user')
    def set_password(self, password):
        self.password = generate_password_hash(password)
    #counting the cart for both guest users and logged in users
    @property
    def cart_count(self):
        if current_user.is_authenticated:
            return sum(cart_item.quantity for cart_item in self.cart_items)
        else:
            cart = session.get('cart', {})
            return sum(cart.values())

#item class and setting up relationship of cart items
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    cart_items = db.relationship('Cart', back_populates='item')

#cart class with backreferences 
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', back_populates='cart_items')
    item = db.relationship('Item', back_populates='cart_items')

# order class with attributes and relationship
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_items = db.relationship('OrderItem', back_populates='order')

#used for potential order tracking with relationships
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_each = db.Column(db.Float, nullable=False)

    #backreferences for order and item
    order = db.relationship('Order', back_populates='order_items')
    item = db.relationship('Item')