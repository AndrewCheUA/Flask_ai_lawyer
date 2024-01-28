from PIL import Image
from flask import Flask, render_template
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Message
from flask_mail import Mail
from flask_socketio import SocketIO


import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['ALGORITHM'] = os.getenv('ALGORITHM')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')


mail = Mail(app)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def pagination_range(current_page, total_pages, neighbors=2):
    """
    Generates a list of page numbers and ellipses placeholders.
    :param current_page: The current active page.
    :param total_pages: The total number of pages.
    :param neighbors: Number of pages to show around the current page.
    :return: A list with page numbers and ellipses.
    """
    result = []
    for i in range(1, total_pages + 1):
        if i == 1 or i == total_pages or \
                i >= current_page - neighbors and i <= current_page + neighbors:
            result.append(i)
        elif result[-1] != '...':
            result.append('...')
    return result


def send_reset_email(user):
    with app.app_context():
        token = user.get_reset_token()
        msg = Message(subject='Password Reset Request',
                      recipients=[user.email],
                      body=None,
                      html=None,
                      sender=('KURWA BOBR', app.config['MAIL_USERNAME']))
        msg.body = render_template('email/reset_password.txt', user=user, token=token)
        msg.html = render_template('email/reset_password.html', user=user, token=token)

        # Send the message within the application context
        mail.send(msg)



def send_confirm_email(user):
    with app.app_context():
        token = user.get_reset_token(expires_in=60000)
        msg = Message(subject='Email Confirm Request',
                      recipients=[user.email],
                      body=None,
                      html=None,
                      sender=('KURWA BOBR', app.config['MAIL_USERNAME']))
        msg.body = render_template('email/confirm_email.txt', user=user, token=token)
        msg.html = render_template('email/confirm_email.html', user=user, token=token)

        # Send the message within the application context
        mail.send(msg)