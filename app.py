from flask import Flask, render_template, redirect, flash, session, url_for
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.app_context().push()

connect_db(app)
db.create_all()


@app.route('/')
def index_page():
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register_user():

    if "user_id" in session:
        return redirect(f"/users/{session['user_id']}")

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Try a different username')
            return render_template('register.html', form=form)
        session['user_id'] = new_user.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f"/users/{new_user.username}")

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():

    if "user_id" in session:
        return redirect(f"/users/{session['user_id']}")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['user_id'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ['Invalid username/password.']
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash("Goodbye!", "info")
    return redirect('/')


@app.route('/users/<username>')
def secret_page(username):
    if 'user_id' not in session or username != session['user_id']:
        flash("Please log in first!", "danger")
        return redirect("/login")

    user = User.query.get(username)
    form = DeleteForm()

    return render_template("show.html", user=user, form=form)


@app.route("/users/<username>/delete", methods=["POST"])
def remove_user(username):
    """Remove user nad redirect to login."""

    if "user_id" not in session or username != session['user_id']:
        flash("Please log in first!", "danger")
        return redirect("/login")

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("user_id")

    return redirect("/login")


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    """Show add-feedback form and process it."""

    if "user_id" not in session or username != session['user_id']:
        flash("Please log in first!", "danger")
        return redirect("/login")

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")
    else:
        return render_template("new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "user_id" not in session or feedback.username != session['user_id']:
        flash("Please log in first!", "danger")
        return redirect("/login")

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "user_id" not in session or feedback.username != session['user_id']:
        flash("Please log in first!", "danger")
        return redirect("/login")

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")


