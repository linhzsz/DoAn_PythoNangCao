from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Model người dùng
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("Email hoặc Username đã tồn tại. Vui lòng chọn email hoặc username khác.", "danger")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            print(f"Logged in user: {username}")  
            return redirect(url_for('index'))
        else:
            print(f"Failed login attempt: {username}")  
            flash("Thông tin đăng nhập không hợp lệ. Vui lòng thử lại.", "danger")

    return render_template('login.html')


# Route trang chủ
@app.route('/')
def index():
    weather_london = get_weather('London, GB')
    weather_tokyo = get_weather('Tokyo, JP')
    weather_washington = get_weather('Washington, US')

    return render_template('index.html', 
                           weather_london=weather_london,
                           weather_tokyo=weather_tokyo,
                           weather_washington=weather_washington,
                           weather=None)

# Đăng xuất
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for('login'))

# Weather API functions
API_KEY = '2ea01d4a21ee04a2e177a4845f087882'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

def get_weather(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'vi'
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/search', methods=['POST'])
def search():
    city_input = request.form.get('city')
    weather_data = get_weather(city_input)
    if weather_data:
        return render_template('index.html', 
                               weather_london=get_weather('London, GB'),
                               weather_tokyo=get_weather('Tokyo, JP'),
                               weather_washington=get_weather('Washington, US'),
                               weather=weather_data)
    else:
        return render_template('index.html', 
                               weather_london=get_weather('London, GB'),
                               weather_tokyo=get_weather('Tokyo, JP'),
                               weather_washington=get_weather('Washington, US'),
                               weather=None,
                               error="Không tìm thấy thông tin thời tiết cho thành phố đã nhập.")

if __name__ == '__main__':
    app.run(debug=True)
