from flask import render_template, url_for, flash, redirect, request, session
from flask_login import login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, \
    ConfirmEmailForm
from system import app, login_manager, bcrypt, save_picture, pagination_range, send_reset_email, send_confirm_email

from flask_socketio import SocketIO, join_room, leave_room, send

from database.sql_db.models import User, Post
from database.sql_db.connect import session_db

socketio = SocketIO(app)
rooms = {}

@login_manager.user_loader
def load_user(user_id):
    return session_db.query(User).filter_by(id=user_id).first()


@app.route("/", methods=["POST", "GET"])
@app.route("/home", methods=["POST", "GET"])
def home():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    total_posts = session_db.query(Post).count()
    posts = session_db.query(Post).order_by(Post.date_posted.asc()).offset(offset).limit(per_page).all()
    total_pages = (total_posts // per_page) + (1 if total_posts % per_page else 0)
    pagination = pagination_range(page, total_pages)

    if request.method == "POST":
        name = current_user.username

        room = "AAAA"
        rooms[room] = {"members": 0, "messages": []}


        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    return render_template('home.html', posts=posts, page=page, total_pages=total_pages, pagination_range=pagination)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        session_db.add(user)
        session_db.commit()
        send_confirm_email(user)
        flash('Please check your email address for a confirmation link.', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()

    if form.validate_on_submit():
        user = session_db.query(User).filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.is_active == False:
                logout_user()
                flash('Your email is not confirmed. Please confirm your email!', 'danger')
                return redirect(url_for('home'))

            flash('Login Successful.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    previous_email = current_user.email
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        user = session_db.query(User).filter_by(username=current_user.username).first()
        user.username = form.username.data
        user.email = form.email.data
        if previous_email != form.email.data:
            user.is_active = False
            send_confirm_email(user)

        session_db.commit()

        flash('Your account has been updated!', 'success')
        logout_user()
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)
        session_db.add(post)
        session_db.commit()
        flash('Your post has been posted!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New post', form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = session_db.get(Post, post_id)
    return render_template('post.html', title='New post', post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = session_db.get(Post, post_id)
    if post.user != current_user:
        flash('You dont have the permission to edit others posts!', 'danger')
        return redirect(url_for('home'))
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        session_db.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = session_db.get(Post, post_id)
    if post.user != current_user:
        flash('You dont have the permission to delete others posts!', 'danger')
        return redirect(url_for('home'))
    session_db.delete(post)
    session_db.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    total_posts = session_db.query(Post).join(User).filter(User.username == username).count()
    posts = session_db.query(Post).join(User).filter(User.username == username).order_by(Post.date_posted.asc()).offset(
        offset).limit(per_page).all()
    total_pages = (total_posts // per_page) + (1 if total_posts % per_page else 0)
    pagination = pagination_range(page, total_pages)

    user = session_db.query(User).filter_by(username=username).first()

    return render_template('user_posts.html', posts=posts, page=page, total_pages=total_pages, user=user,
                           pagination_range=pagination, total_posts=total_posts)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = session_db.query(User).filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('home'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        session_db.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/confirm_mail/<token>", methods=['GET', 'POST'])
def confirm_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('home'))

    form = ConfirmEmailForm()

    if form.validate_on_submit():
        user.is_active = True
        session_db.commit()
        flash('Your Email is confirmed.', 'info')
        return redirect(url_for('login'))
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    return render_template('confirm_email.html', title='Confirm Email', form=form, user=user, image_file=image_file)


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("chat/room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
