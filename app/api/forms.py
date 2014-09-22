import wtforms_json
from wtforms import Form, StringField, PasswordField, TextAreaField, validators

wtforms_json.init()


class RegisterForm(Form):
    username = StringField('username', [validators.Length(min=4, max=20)])
    password = PasswordField('password', [validators.Length(min=4, max=30)])
    repassword = PasswordField('re-password',
                               [validators.Length(min=4, max=30),
                                validators.Optional()])


class ThreadForm(Form):
    title = StringField('title', [validators.Length(min=5, max=50)])
    body = TextAreaField('body', [validators.Length(min=50, max=5000)])