from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    cart = db.relationship('CartItem', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

#Routes
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price} for p in products])

@app.route('/products', methods=['POST'])
def add_product():
    data = request.json
    new_product = Product(name=data['name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'id': new_product.id, 'name': new_product.name, 'price': new_product.price}), 201

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in customers])

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    new_customer = Customer(name=data['name'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'id': new_customer.id, 'name': new_customer.name}), 201

@app.route('/customers/<int:customer_id>/cart', methods=['POST'])
def add_to_cart(customer_id):
    data = request.json
    customer = Customer.query.get_or_404(customer_id)
    product = Product.query.get_or_404(data['product_id'])
    cart_item = CartItem(customer_id=customer.id, product_id=product.id, quantity=data['quantity'])
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'customer_id': cart_item.customer_id, 'product_id': cart_item.product_id, 'quantity': cart_item.quantity}), 201

@app.route('/customers/<int:customer_id>/cart', methods=['GET'])
def view_cart(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    cart_items = CartItem.query.filter_by(customer_id=customer.id).all()
    cart_details = [{'product_id': item.product_id, 'quantity': item.quantity} for item in cart_items]
    return jsonify(cart_details)

@app.route('/customers/<int:customer_id>/checkout', methods=['POST'])
def checkout(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    cart_items = CartItem.query.filter_by(customer_id=customer.id).all()
    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400

    total_amount = sum(item.quantity * item.product.price for item in cart_items)
    new_order = Order(customer_id=customer.id, total_amount=total_amount)
    db.session.add(new_order)
    CartItem.query.filter_by(customer_id=customer.id).delete()
    db.session.commit()
    return jsonify({'order_id': new_order.id, 'total_amount': new_order.total_amount}), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([{'id': o.id, 'customer_id': o.customer_id, 'total_amount': o.total_amount} for o in orders])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
