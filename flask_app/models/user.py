from flask import flash, session
from flask_app.models.model_base import ModelBase
from flask_app.config.mysqlconnection import connectToMySQL
from flask_app import bcrypt
import re


class User(ModelBase):
    table = "users"
    fields = [
        "username",
        "email",
        "password_hash",
    ]

    valid_email_format = re.compile(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$")
    password_min_length = 8

    @classmethod
    def create(self, form_data):
        data = {**form_data}
        data["email"] = data["email"].lower()
        data["password_hash"] = bcrypt.generate_password_hash(data["password"], 12)
        return super().create(data)

    @classmethod
    def get_by_email(cls, email: str):
        query = f"SELECT * FROM {cls.table} WHERE email = %(email)s;"
        view = connectToMySQL(cls.db).query_db(query, {"email": email.lower()})
        return cls(view[0]) if view else None

    @classmethod
    def authenticate_to_id(cls, data):
        target_user = cls.get_by_email(data["email"])
        if target_user is None:
            flash("Username or password not valid", "login-error")
            return None
        elif not bcrypt.check_password_hash(target_user.password_hash, data["password"]):
            flash("Username or password not valid", "login-error")
            return None
        else:
            return target_user.id

    @classmethod
    def validate_form_input(cls, data) -> bool:
        is_valid = True

        # Presence of data

        if "username" not in data:
            flash("Please submit a username", "validate-username-error")
            is_valid = False

        if "email" not in data:
            flash("You must provide an email address", "validate-email-error")
            is_valid = False

        if "password" not in data:
            flash("You must provide a password.", "validate-password-error")
            is_valid = False

        if "confirm-password" not in data:
            flash("You must provide a password confirmation.", "validate-password-error")
            is_valid = False

        # Form of data

        if not data["username"].isalnum():
            flash("Username must not contain non-alphanumeric characters", "validate-username-error")
            is_valid = False

        if len(data["username"]) < 2:
            flash("Username must be at least two characters long", "validate-username-error")
            is_valid = False

        if not cls.valid_email_format.match(data["email"]):
            flash("Email provided is not valid.", "validate-email-error")
            is_valid = False

        if data["password"] != data["confirm-password"]:
            flash("Password confirmation does not match!", "validate-password-error")
            is_valid = False

        if len(data["password"]) < cls.password_min_length:
            flash("Password must be at least 8 characters", "validate-password-error")
            is_valid = False

        if not cls.is_strong_password(data["password"]):
            flash("Your password is weak babysauce, only chad passwords allowed", "validate-password-error")
            is_valid = False

        # Duplicates

        if "id" not in data and cls.get_by_email(data["email"]) is not None:
            flash(f"Email address {data['email']} is already in use, please login", "validate-email-error")
            is_valid = False

        if not is_valid:
            session["redo"] = data

        return is_valid

    @staticmethod
    def is_strong_password(password: str) -> bool:
        class Checks:  # having a 'var' keyword would elide shit like this, thanks python
            has_alpha = False
            has_upper = False
            has_lower = False
            has_numeric = False
            has_special = False

        for char in password:
            if char.isalpha():
                Checks.has_alpha = True
                if char.isupper():
                    Checks.has_upper = True
                elif char.islower():
                    Checks.has_lower = True
            elif char.isnumeric():
                Checks.has_numeric = True
            elif char.isprintable():
                Checks.has_special = True

        return Checks.has_alpha \
            and Checks.has_upper \
            and Checks.has_lower \
            and Checks.has_numeric \
            and Checks.has_special
