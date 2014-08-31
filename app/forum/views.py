from flask import Blueprint, request, session, g, redirect, url_for, abort, \
                  render_template, flash, make_response

from .forms import RegisterForm

forum = Blueprint('forum', __name__)


@forum.route('/')
def index():
    return render_template('forum.html')



@forum.route('/user')
def user():
    form = RegisterForm()
    return render_template('user.html', form=form)


@forum.route('/login', methods=['GET', 'POST'])
def login():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        repassword = form.repassword.data

        if repassword:
            if password == repassword:
                # create account
                # login
                flash('Account created')
            form.errors['re-password'] = ['Password does not match']
            return render_template('login.html', form=form)
                
        # login

    return render_template('login.html', form=form)

