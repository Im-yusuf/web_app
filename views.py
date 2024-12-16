#all imports we need for the application
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user,current_user
from werkzeug.security import check_password_hash
from app import db
from app.models import User, Item, Cart
from app.forms import LoginForm, RegistrationForm

#main routes registering for application 
def register_routes(app):
    #to add login forms into every template
    @app.context_processor
    def inject_forms():
        return {'form': LoginForm(),'register_form': RegistrationForm()}
    #main route/home with redirect to home.html
    @app.route('/')
    def index():
        login_form = LoginForm()
        register_form = RegistrationForm()
        items = Item.query.all()
        next_page = request.args.get('next', request.path)
        return render_template('home.html', items=items, form=login_form, register_form=register_form, next=next_page)

    #registration route when form submitted via post
    @app.route('/register', methods=['POST'])
    def register():
        register_form = RegistrationForm()

        if register_form.validate_on_submit():
            existing_user = User.query.filter_by(email=register_form.email.data).first()
            if existing_user:
                flash('Email in use, use another email', 'danger')
                return redirect(url_for('index', login_failed=True))

            existing_username = User.query.filter_by(username=register_form.username.data).first()
            if existing_username:
                flash('Username taken,sorry pal', 'danger')
                return redirect(url_for('index', login_failed=True))
            
            new_user = User(username=register_form.username.data,email=register_form.email.data)
            new_user.set_password(register_form.password.data)

            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('index'))
            except Exception:
                flash('An error occurred when making user', 'danger')
                return redirect(url_for('index', login_failed=True))
        
        flash('Registration failed, please use different credentials', 'danger')
        return redirect(url_for('index', login_failed=True))
    
    #login route active when form submitted via post 
    @app.route('/login', methods=['POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('Logged in!!!', 'success')

                # making session cart into user cart
                session_cart = session.get('cart', {})
                #incrementing cart item quantity
                for item_id, quantity in session_cart.items():
                    cart_item = Cart.query.filter_by(user_id=user.id, item_id=item_id).first()
                    if cart_item:
                        cart_item.quantity += quantity
                    else:
                        new_cart_item = Cart(user_id=user.id, item_id=item_id, quantity=quantity)
                        db.session.add(new_cart_item)
                db.session.commit()
                session.pop('cart', None)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid Credentials', 'danger')
        else:
            flash('Couldnt validate form', 'warning')
        return redirect(url_for('index'))

    #logout route to log the user out when they press logout 
    @app.route('/logout', methods=['POST'])
    def logout():
        logout_user()
        flash('Succesfully logged out', 'success')
        return redirect(url_for('index'))

    #adding to cart route from home page 
    @app.route('/add_to_cart/<int:item_id>', methods=['POST'])
    def add_to_cart(item_id):
        item = Item.query.get(item_id)
        adding_quantity = int(request.form.get('quantity', 1))

        #handling for both logged in and as guest
        if current_user.is_authenticated:
            existing_cart_item = Cart.query.filter_by(user_id=current_user.id, item_id=item_id).first()
            existing_quantity = existing_cart_item.quantity if existing_cart_item else 0
        else:
            cart = session.get('cart', {})
            existing_quantity = cart.get(str(item_id), 0)

        total_quantity_after_add = existing_quantity + adding_quantity
        if item.stock < total_quantity_after_add:
            flash(f'Not enough {item.name},you have {existing_quantity} in your cart', 'warning')
            return redirect(url_for('index'))

        #incrementing cart quantity 
        if current_user.is_authenticated:
            if existing_cart_item:
                existing_cart_item.quantity = total_quantity_after_add
            else:
                new_cart_item = Cart(user_id=current_user.id, item_id=item_id, quantity=adding_quantity)
                db.session.add(new_cart_item)
            db.session.commit()
        else:
            cart[str(item_id)] = total_quantity_after_add
            session['cart'] = cart

        flash(f"{item.name} added to cart!!!!", "success")
        return redirect(url_for('index'))
    
    #cart route and logic
    @app.route('/cart')
    def cart():
        cart_items = []
        total_price = 0

        #cart for both logged in and guest
        if current_user.is_authenticated:
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            total_price = sum(item.item.price * item.quantity for item in cart_items)
            total_items = sum(item.quantity for item in cart_items)
        else:
            session_cart = session.get('cart', {})
            for item_id, quantity in session_cart.items():
                item = Item.query.get(int(item_id))
                if item:
                    cart_items.append({'item': item, 'quantity': quantity})
                    total_price += item.price * quantity
            total_items = sum(session_cart.values())
        login_form = LoginForm()
        register_form = RegistrationForm()
        return render_template('cart.html',cart_items=cart_items,total_price=round(total_price,2),form=login_form,register_form=register_form,total_items=total_items)
    #total calculator for users with login
    def compute_totals_for_user():
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total_price = round(sum(ci.item.price * ci.quantity for ci in cart_items),2)
        total_quantity = sum(ci.quantity for ci in cart_items)
        return total_price, total_quantity
    #logic for computing totals for guests using session details
    def compute_totals_for_guest():
        session_cart = session.get('cart', {})
        total_price = 0
        total_quantity = 0
        for i, qty in session_cart.items():
            item = Item.query.get(int(i))
            if item:
                total_price += item.price * qty
                total_quantity += qty
        total_price=round(total_price,2)
        return total_price, total_quantity
    #ajax function for incrementing cart items
    @app.route('/increase_cart_item_ajax/<int:item_id>', methods=['POST'])
    def increase_cart_item_ajax(item_id):
        #again incrementing for guest/user
        if current_user.is_authenticated:
            cart_item = Cart.query.filter_by(user_id=current_user.id, item_id=item_id).first()
            if cart_item:
                cart_item.quantity += 1
                db.session.commit()
            total_price, total_quantity = compute_totals_for_user()
            return {'status': 'success','item_id': item_id,'new_quantity': cart_item.quantity if cart_item else 0,'item_subtotal': round((cart_item.item.price * cart_item.quantity),2) if cart_item else 0,'total_price': round(total_price,2),'total_quantity': total_quantity}
        else:
            cart = session.get('cart', {})
            item_id_str = str(item_id)
            if item_id_str in cart:
                cart[item_id_str] += 1
                session['cart'] = cart
            total_price, total_quantity = compute_totals_for_guest()
            new_quantity = cart.get(item_id_str, 0)
            item = Item.query.get(item_id) if new_quantity else None
            item_subtotal = item.price * new_quantity if item else 0
            return {'status': 'success','item_id': item_id,'new_quantity': new_quantity,'item_subtotal': round(item_subtotal,2),'total_price': round(total_price,2),'total_quantity': total_quantity}
    #ajax feature for decreasing cart items
    @app.route('/decrease_cart_item_ajax/<int:item_id>', methods=['POST'])
    def decrease_cart_item_ajax(item_id):
        #both cases for users and guests
        if current_user.is_authenticated:
            cart_item = Cart.query.filter_by(user_id=current_user.id, item_id=item_id).first()

            item_price = cart_item.item.price if cart_item else 0
            old_quantity = cart_item.quantity if cart_item else 0
            new_quantity = old_quantity - 1 if old_quantity > 1 else 0
            item_subtotal = item_price * new_quantity if new_quantity > 0 else 0
            if cart_item:
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    db.session.commit()
                else:
                    db.session.delete(cart_item)
                    db.session.commit()
            total_price, total_quantity = compute_totals_for_user()

            return {'status': 'success','item_id': item_id,'new_quantity': new_quantity,'item_subtotal': item_subtotal,'total_price': total_price,'total_quantity': total_quantity}
        else:
            cart = session.get('cart', {})
            item_id_string = str(item_id)
            if item_id_string in cart:
                if cart[item_id_string] > 1:
                    cart[item_id_string] -= 1
                else:
                    del cart[item_id_string]
                session['cart'] = cart
            total_price, total_quantity = compute_totals_for_guest()
            new_quantity = cart.get(item_id_string, 0)
            item = Item.query.get(item_id) if new_quantity else None
            item_subtotal = (item.price * new_quantity) if item else 0
            return {'status': 'success','item_id': item_id,'new_quantity': new_quantity,'item_subtotal': item_subtotal,'total_price': total_price,'total_quantity': total_quantity}
    #logicx for removing a whole lot of items and then commiting to database
    @app.route('/remove_item_entirely_ajax/<int:item_id>', methods=['POST'])
    def remove_item_entirely_ajax(item_id):
        if current_user.is_authenticated:
            cart_item = Cart.query.filter_by(user_id=current_user.id, item_id=item_id).first()
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
            total_price, total_quantity = compute_totals_for_user()
            return {'status': 'success','item_id': item_id,'new_quantity': 0,'item_subtotal': 0,'total_price': round(total_price,2),'total_quantity': total_quantity}
        else:
            cart = session.get('cart', {})
            item_id_str = str(item_id)
            if item_id_str in cart:
                del cart[item_id_str]
                session['cart'] = cart
            total_price, total_quantity = compute_totals_for_guest()
            return {'status': 'success','item_id': item_id,'new_quantity': 0,'item_subtotal': 0,'total_price': round(total_price,2),'total_quantity': total_quantity}
    #checkout logic with billing and delivery adress
    @app.route('/checkout', methods=['POST'])
    def checkout():
        try:
            billing_address = request.form.get('billing_address')
            delivery_address = request.form.get('delivery_address')

            if not billing_address or not delivery_address:
                flash("Enter billing and delviery adress!!", "danger")
                return redirect(url_for('cart'))
            cart_items = []
            if current_user.is_authenticated:
                cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            else:
                session_cart = session.get('cart', {})
                cart_items = [{"item": Item.query.get(int(item_id)), "quantity": quantity}
                            for item_id, quantity in session_cart.items()]
            # update stock for each item in the cart
            for cart_item in cart_items:
                item = cart_item.item if hasattr(cart_item, "item") else cart_item["item"]
                quantity = cart_item.quantity if hasattr(cart_item, "quantity") else cart_item["quantity"]

                if not item or item.stock < quantity:
                    flash(f"Insufficient stock for {item.name}.", "danger")
                    return redirect(url_for('cart'))
                item.stock -= quantity
            db.session.commit()
            # clearing the cart after order placed
            if current_user.is_authenticated:
                for cart_item in cart_items:
                    db.session.delete(cart_item)
            else:
                session.pop('cart', None)
            db.session.commit()
            flash("Order placed!!!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('cart'))
