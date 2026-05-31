
from flask import Flask, render_template_string, request, redirect, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'bouquetparcel'

# ================= CONFIG =================

UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ================= DATABASE =================

def connect_db():

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    return conn

def init_db():

    conn = connect_db()
    cur = conn.cursor()

    # USERS
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    ''')

    # PRODUCTS
    cur.execute('''
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        description TEXT,
        image TEXT,
        seller_id INTEGER
    )
    ''')

    # ORDERS
    cur.execute('''
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        seller_id INTEGER,
        product_name TEXT,
        total INTEGER,
        address TEXT,
        phone TEXT,
        payment TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()



# ================= CART =================

cart = []

# ================= TEMPLATE =================

base_template = '''

<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Bouquet Parcel Lombok Timur</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
    background:#ffe6f0;
    font-family:Arial;
}

.navbar{
    background:#ff4f9a;
}

.navbar-brand{
    font-size:24px;
    font-weight:bold;
}

.hero{
    background:linear-gradient(to right,#ff4f9a,#ff85b3);
    color:white;
    padding:80px 20px;
    border-radius:25px;
    text-align:center;
    margin-bottom:40px;
}

.hero img{
    width:150px;
    margin-bottom:20px;
}

.hero h1{
    font-size:50px;
    font-weight:bold;
}

.card{
    border:none;
    border-radius:20px;
    overflow:hidden;
    box-shadow:0 0 15px rgba(0,0,0,0.1);
}

.card img{
    width:100%;
    height:250px;
    object-fit:cover;
}

.btn-primary{
    background:#ff4f9a;
    border:none;
}

.btn-primary:hover{
    background:#ff2f85;
}

.login-box{
    width:420px;
    background:white;
    padding:40px;
    border-radius:25px;
    margin:auto;
    margin-top:50px;
    box-shadow:0 0 20px rgba(0,0,0,0.2);
}

.form-control{
    border-radius:12px;
    padding:12px;
}

.btn{
    border-radius:12px;
}

table{
    background:white;
}

@media(max-width:768px){

.hero h1{
    font-size:30px;
}

.login-box{
    width:95%;
}

.card img{
    height:200px;
}

}

</style>

</head>

<body>

<nav class="navbar navbar-expand-lg navbar-dark p-3">

<div class="container">

<a class="navbar-brand" href="/">
🌸 Bouquet Parcel Lombok Timur
</a>

<div>

{% if session.get('username') %}

<span class="text-white me-3">
Halo, {{ session['username'] }}
</span>

{% if session['role'] == 'admin' %}
<a href="/admin" class="btn btn-warning">Admin</a>
{% endif %}

{% if session['role'] == 'penjual' %}
<a href="/seller" class="btn btn-info">Dashboard Jualan</a>
<a href="/add_product" class="btn btn-primary">Tambah Produk</a>
<a href="/seller_orders" class="btn btn-success">Pesanan Masuk</a>
{% endif %}

<a href="/cart" class="btn btn-success">Cart</a>
<a href="/orders" class="btn btn-light">Orders</a>
<a href="/logout" class="btn btn-danger">Logout</a>

{% else %}

<a href="/login" class="btn btn-light">Login</a>
<a href="/register" class="btn btn-warning">Register</a>

{% endif %}

</div>

</div>

</nav>

<div class="container mt-4">

{% with messages = get_flashed_messages() %}
{% if messages %}
{% for msg in messages %}

<div class="alert alert-success">
{{ msg }}
</div>

{% endfor %}
{% endif %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>

'''

# ================= HOME =================

@app.route('/')
def index():

    conn = connect_db()

    keyword = request.args.get('search')

    if keyword:

        products = conn.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            ('%' + keyword + '%',)
        ).fetchall()

    else:

        products = conn.execute(
            "SELECT * FROM products"
        ).fetchall()

    conn.close()

    html = '''

    <div class="hero">

        <img src="/static/uploads/logo.png">

        <h1>Bouquet Parcel Lombok Timur</h1>

        <p>
            Bouquet • Parcel • Wisuda • Ulang Tahun 💖
        </p>

    </div>

    <form method="GET">

        <input type="text"
               name="search"
               class="form-control mb-4"
               placeholder="Cari bouquet favoritmu...">

    </form>

    <div class="row">

    {% for p in products %}

    <div class="col-md-4 mb-4">

        <div class="card">

            <img src="/static/uploads/{{ p['image'] }}">

            <div class="card-body">

                <h4>{{ p['name'] }}</h4>

                <h5 class="text-danger">
                    Rp {{ p['price'] }}
                </h5>

                <p>{{ p['description'] }}</p>

                <a href="/add_to_cart/{{ p['id'] }}"
                   class="btn btn-primary w-100">

                   Tambah ke Keranjang

                </a>

            </div>

        </div>

    </div>

    {% endfor %}

    </div>

    '''

    content = render_template_string(html, products=products)

    return render_template_string(base_template, content=content)

# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = connect_db()

        conn.execute(
            "INSERT INTO users(username,password,role) VALUES(?,?,?)",
            (username,password,role)
        )

        conn.commit()
        conn.close()

        flash('Register berhasil')

        return redirect('/login')

    html = '''

    <div class="login-box">

        <h2 class="text-danger text-center mb-4">
            Register
        </h2>

        <form method="POST">

            <input type="text"
                   name="username"
                   class="form-control mb-3"
                   placeholder="Username"
                   required>

            <input type="password"
                   name="password"
                   class="form-control mb-3"
                   placeholder="Password"
                   required>

            <select name="role"
                    class="form-control mb-3">

                <option value="pembeli">Pembeli</option>
                <option value="penjual">Penjual</option>

            </select>

            <button class="btn btn-primary w-100">
                Register
            </button>

        </form>

    </div>

    '''

    content = render_template_string(html)

    return render_template_string(base_template, content=content)

# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = connect_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()

        conn.close()

        if user:

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'penjual':
                return redirect('/seller')

            return redirect('/')

        flash('Username atau Password salah')

    html = '''

    <div class="login-box">

        <h1 class="text-danger text-center">
            Bouquet Parcel Lombok Timur
        </h1>

        <p class="text-center">
            Marketplace Bouquet Modern 💖
        </p>

        <form method="POST">

            <input type="text"
                   name="username"
                   class="form-control mb-3"
                   placeholder="Username"
                   required>

            <input type="password"
                   name="password"
                   class="form-control mb-3"
                   placeholder="Password"
                   required>

            <button class="btn btn-primary w-100">
                Login
            </button>

        </form>

    </div>

    '''

    content = render_template_string(html)

    return render_template_string(base_template, content=content)

# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ================= SELLER =================

@app.route('/seller')
def seller():

    if session.get('role') != 'penjual':
        return redirect('/login')

    conn = connect_db()

    products = conn.execute(
        "SELECT * FROM products WHERE seller_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    html = '''

    <h2 class="mb-4">
        Dashboard Penjual
    </h2>

    <div class="row">

    {% for p in products %}

    <div class="col-md-4 mb-4">

        <div class="card">

            <img src="/static/uploads/{{ p['image'] }}">

            <div class="card-body">

                <h4>{{ p['name'] }}</h4>

                <h5 class="text-danger">
                    Rp {{ p['price'] }}
                </h5>

                <p>{{ p['description'] }}</p>

                <a href="/delete_product/{{ p['id'] }}"
                   class="btn btn-danger w-100">

                   Hapus Produk

                </a>

            </div>

        </div>

    </div>

    {% endfor %}

    </div>

    '''

    content = render_template_string(html, products=products)

    return render_template_string(base_template, content=content)

# ================= ADD PRODUCT =================

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    if session.get('role') != 'penjual':
        return redirect('/login')

    if request.method == 'POST':

        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        image = request.files['image']

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(app.config['UPLOAD_FOLDER'], filename)
        )

        conn = connect_db()

        conn.execute('''
        INSERT INTO products(
            name,
            price,
            description,
            image,
            seller_id
        )
        VALUES(?,?,?,?,?)
        ''', (
            name,
            price,
            description,
            filename,
            session['user_id']
        ))

        conn.commit()
        conn.close()

        flash('Produk berhasil ditambahkan')

        return redirect('/seller')

    html = '''

    <div class="login-box">

        <h2 class="text-danger text-center mb-4">
            Tambah Produk
        </h2>

        <form method="POST" enctype="multipart/form-data">

            <input type="text"
                   name="name"
                   class="form-control mb-3"
                   placeholder="Nama Bouquet"
                   required>

            <input type="number"
                   name="price"
                   class="form-control mb-3"
                   placeholder="Harga"
                   required>

            <textarea name="description"
                      class="form-control mb-3"
                      placeholder="Deskripsi"></textarea>

            <input type="file"
                   name="image"
                   class="form-control mb-3"
                   required>

            <button class="btn btn-primary w-100">
                Simpan Produk
            </button>

        </form>

    </div>

    '''

    content = render_template_string(html)

    return render_template_string(base_template, content=content)

# ================= DELETE PRODUCT =================

@app.route('/delete_product/<int:id>')
def delete_product(id):

    conn = connect_db()

    conn.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash('Produk berhasil dihapus')

    return redirect('/seller')

# ================= CART =================

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    conn = connect_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    if product:
        cart.append(dict(product))

    flash('Produk masuk keranjang')

    return redirect('/')

@app.route('/cart')
def view_cart():

    total = sum(int(item['price']) for item in cart)

    html = '''

    <h2 class="mb-4">
        Keranjang Belanja
    </h2>

    <table class="table table-bordered">

        <tr>
            <th>Produk</th>
            <th>Harga</th>
        </tr>

        {% for item in cart %}

        <tr>
            <td>{{ item['name'] }}</td>
            <td>Rp {{ item['price'] }}</td>
        </tr>

        {% endfor %}

    </table>

    <h3 class="text-danger">
        Total : Rp {{ total }}
    </h3>

    <a href="/checkout" class="btn btn-success">
       Checkout
    </a>

    '''

    content = render_template_string(
        html,
        cart=cart,
        total=total
    )

    return render_template_string(base_template, content=content)

# ================= CHECKOUT =================

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():

    if 'user_id' not in session:
        return redirect('/login')

    if len(cart) == 0:
        flash('Keranjang kosong')
        return redirect('/')

    if request.method == 'POST':

        address = request.form['address']
        phone = request.form['phone']
        payment = request.form['payment']

        conn = connect_db()

        for item in cart:

            conn.execute('''
            INSERT INTO orders(
                user_id,
                seller_id,
                product_name,
                total,
                address,
                phone,
                payment,
                status
            )
            VALUES(?,?,?,?,?,?,?,?)
            ''', (
                session['user_id'],
                item['seller_id'],
                item['name'],
                item['price'],
                address,
                phone,
                payment,
                'Pesanan Baru'
            ))

        conn.commit()
        conn.close()

        cart.clear()

        flash('Checkout berhasil')

        return redirect('/orders')

    html = '''

    <div class="login-box">

        <h2 class="text-danger text-center mb-4">
            Checkout
        </h2>

        <form method="POST">

            <textarea name="address"
                      class="form-control mb-3"
                      placeholder="Alamat Lengkap"
                      required></textarea>

            <input type="text"
                   name="phone"
                   class="form-control mb-3"
                   placeholder="Nomor HP"
                   required>

            <select name="payment"
                    class="form-control mb-3">

                <option value="COD">COD</option>
                <option value="Transfer Bank">Transfer Bank</option>
                <option value="QRIS">QRIS</option>

            </select>

            <button class="btn btn-primary w-100">
                Buat Pesanan
            </button>

        </form>

    </div>

    '''

    content = render_template_string(html)

    return render_template_string(base_template, content=content)

# ================= ORDERS =================

@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect('/login')

    conn = connect_db()

    data = conn.execute(
        "SELECT * FROM orders WHERE user_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    html = '''

    <h2 class="mb-4">
        Riwayat Pesanan
    </h2>

    <table class="table table-bordered">

        <tr>
            <th>Produk</th>
            <th>Total</th>
            <th>Status</th>
        </tr>

        {% for o in orders %}

        <tr>

            <td>{{ o['product_name'] }}</td>

            <td>
                Rp {{ o['total'] }}
            </td>

            <td>{{ o['status'] }}</td>

        </tr>

        {% endfor %}

    </table>

    '''

    content = render_template_string(
        html,
        orders=data
    )

    return render_template_string(base_template, content=content)

# ================= SELLER ORDERS =================

@app.route('/seller_orders')
def seller_orders():

    if session.get('role') != 'penjual':
        return redirect('/login')

    conn = connect_db()

    orders = conn.execute(
        "SELECT * FROM orders WHERE seller_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    html = '''

    <h2 class="mb-4">
        Pesanan Masuk
    </h2>

    {% if orders %}

    <table class="table table-bordered">

        <tr>
            <th>Produk</th>
            <th>Total</th>
            <th>Alamat</th>
            <th>No HP</th>
            <th>Pembayaran</th>
            <th>Status</th>
        </tr>

        {% for o in orders %}

        <tr>

            <td>{{ o['product_name'] }}</td>

            <td>Rp {{ o['total'] }}</td>

            <td>{{ o['address'] }}</td>

            <td>{{ o['phone'] }}</td>

            <td>{{ o['payment'] }}</td>

            <td>{{ o['status'] }}</td>

        </tr>

        {% endfor %}

    </table>

    {% else %}

    <div class="alert alert-warning">
        Belum ada pesanan masuk
    </div>

    {% endif %}

    '''

    content = render_template_string(
        html,
        orders=orders
    )

    return render_template_string(base_template, content=content)

# ================= RUN =================

if __name__ == '__main__':

    app.run(debug=True)

