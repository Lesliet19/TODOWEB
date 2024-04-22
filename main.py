import os

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap4
from datetime import datetime
import random
from apscheduler.schedulers.background import BackgroundScheduler
from flask_wtf import FlaskForm
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from forms import TaskForm, LoginForm, RegisterForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
database = SQLAlchemy(app)

bootstrap = Bootstrap4(app)
current_quote = None

# Define models
class Todo(database.Model):
    __tablename__ = "todo"
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String, unique=False, nullable=False)
    description = database.Column(database.String(150), nullable=False)
    date_created = database.Column(database.String, nullable=False)
    account_id = database.Column(database.Integer, database.ForeignKey('account.id'))

class Account(database.Model, UserMixin):
    __tablename__ = "account"
    id = database.Column(database.Integer, primary_key=True)
    password = database.Column(database.String)
    name = database.Column(database.String)
    email = database.Column(database.String, unique=True)

# Create or update the database schema within the application context
with app.app_context():
    database.create_all()
    database.session.commit()

# Scheduler for generating new quotes
quotes_list = ["You will face many defeats in life, but never let yourself be defeated. – Maya Angelou",
"In three words I can sum up everything I've learned about life: It goes on. – Robert Frost",
"Life is a long lesson in humility. – J.M. Barrie, The Little Minister",
"To live is the rarest thing in the world. Most people exist, that is all. – Oscar Wilde",
"The most important thing is to enjoy your life–to be happy–it's all that matters. – Audrey Hepburn",
"To succeed in life, you need three things: a wishbone, a backbone and a funnybone. – Reba McEntire",
"We must be willing to let go of the life we planned so as to have the life that is waiting for us. – Joseph Campbell",
"Life is a succession of lessons which must be lived to be understood. – Ralph Waldo Emerson",
"Love the life you live. Live the life you love. – Bob Marley",
"I was taught that the way of progress was neither swift nor easy. – Marie Curie",
"He who has a why to live for can bear almost any how. – Friedrich Nietzsche",
"You only live once, but if you do it right, once is enough. – Mae West",
"The whole secret of a successful life is to find out what is one's destiny to do, and then do it. – Henry Ford",
"In order to write about life first you must live it. – Ernest Hemingway",
"Life has no limitations, except the ones you make. – Les Brown",
"It's your outlook on life that counts. If you take yourself lightly and don't take yourself too seriously, pretty soon you can find the humor in our everyday lives. And sometimes it can be a lifesaver. – Betty White",
"Live for each second without hesitation. – Elton John",
"The most wasted of all days is one without laughter. – E. E. Cummings",
"Start each day with a positive thought and a grateful heart. – Roy Bennett",
"All you need in this life is ignorance and confidence; then success is sure. – Mark Twain",
"I believe that if you'll just stand up and go, life will open up for you. Something just motivates you to keep moving. – Tina Turner",
"Many of life's failures are people who did not realize how close they were to success when they gave up. – Thomas Edison",
"I have very strong feelings about how you lead your life. You always look ahead, you never look back. – Ann Richards",
"Life is like riding a bicycle. To keep your balance, you must keep moving. – Albert Einstein",
"Life shrinks or expands in proportion to one's courage. – Anais Nin",
"You do not find the happy life. You make it. – Camilla Eyring Kimball",
"A life is not important except in the impact it has on other lives. – Jackie Robinson",
"The purpose of life is to live it, to taste experience to the utmost, to reach out eagerly and without fear for newer and richer experience. – Eleanor Roosevelt"]

def gen_quote():
    global current_quote
    current_quote = random.choice(quotes_list)

scheduler = BackgroundScheduler()
scheduler.add_job(func=gen_quote, trigger="interval", hours=24)
scheduler.start()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(account_id):
    return Account.query.get(account_id)

# Routes and other functions...
now = datetime.now()
FORMAT_TIME =  now.strftime('%A %B %d')

with app.app_context():
    todos = Todo.query.all()
    for todo in todos:
        print(todo.account_id)
        database.session.commit()



@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/')
def home():
    todos = Todo.query.all()
    global current_quote
    if current_quote is None:
        gen_quote()
    return render_template('home.html', current_date_time=FORMAT_TIME, quote=current_quote, all_tasks=todos, user=current_user)



@app.route('/create-task', methods=['POST', 'GET'])
@login_required
def create_task():
    now = datetime.now()
    form = TaskForm()
    if form.validate_on_submit():
        new_task = Todo(
            title=form.title.data,
            description=form.description.data,
            date_created=now.strftime("%A, %B, %d"),
            account_id=current_user.id
        )
        database.session.add(new_task)
        database.session.commit()
        return redirect(url_for('home'))
    return render_template('task_form.html', form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    users = Account.query.all()
    if form.validate_on_submit():
        password_entered = form.data['password']
        new_user = Account(
            email=form.data['email'],
            password=generate_password_hash(password=password_entered, method='pbkdf2:sha256', salt_length=10),
            name=form.data['name']
        )
        user = Account.query.filter_by(email=new_user.email).first()
        if user in users:
            flash('This user already exists, please login')
        else:
            database.session.add(new_user)
            database.session.commit()
            session.permanent = True

            flash('You have successfully registered yourself ')
            return redirect(url_for('home'))
    return render_template('register.html', form=form)


from flask import render_template, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import check_password_hash

from flask_login import current_user, login_required

@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email_entered = login_form.email.data
        password_entered = login_form.password.data
        user = Account.query.filter_by(email=email_entered).first()
        all_emails = (user.email for user in Account.query.all())
        if user and check_password_hash(user.password, password_entered):
            login_user(user)
            flash(f'Welcome {user.name}, you have successfully logged in!')
            return redirect(url_for('home'))

        elif email_entered not in all_emails:
            flash('This username does not exist. Please register')

        else:
            flash("Invalid email or password")

    return render_template('login.html', form=login_form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    current_user = None
    flash('You have successfully logged out')
    return redirect(url_for('home'))


@app.route('/verify')
def verify():
    return render_template('verify.html')


@app.route('/edit/<todo_id>', methods=['POST', 'GET'])
def edit(todo_id):
    task = database.get_or_404(Todo, todo_id)
    edit_form = TaskForm(
        title=task.title,
        description=task.description,
    )
    if edit_form.validate_on_submit():
        task.title = edit_form.title.data
        task.description = edit_form.description.data
        task.account_id = current_user.id
        database.session.commit()

        flash('You have successfully edited a task!')
        return redirect(url_for('home'))
    return render_template('task_form.html', form=edit_form, task=task)


@app.route("/delete/<int:task_id>", methods=['POST', 'GET'])
@login_required
def delete_post(task_id):
    task_to_delete = database.get_or_404(Todo, task_id)
    database.session.delete(task_to_delete)
    database.session.commit()
    flash('You have successfully deleted a task.')
    return redirect(url_for('home'))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(debug=True)


