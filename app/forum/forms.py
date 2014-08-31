from wtforms import Form, StringField, PasswordField, validators


class RegisterForm(Form):
    username = StringField('username', [validators.Length(min=4, max=20)])
    password = PasswordField('password', [validators.Length(min=4, max=30)])
    repassword = PasswordField('re-password',
                               [validators.Length(min=4, max=30),
                                validators.Optional()])