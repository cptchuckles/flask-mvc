from flask import redirect, session, render_template, flash, request
from flask_app.controllers.controller_base import ControllerBase
from flask_app.models.user import User
from flask_app import app


class UserController(ControllerBase):
    def __init__(self):
        super().__init__(User)

    def register_crud_routes(self):
        super().register_crud_routes()
        return self

    def register_user_auth_routes(self):
        @app.route("/login", methods=["POST"])
        def login():
            if "user_id" in session:
                return redirect("/")

            user_id = User.authenticate_to_id(request.form)
            if user_id is None:
                return redirect("/")

            session["user_id"] = user_id
            return redirect("/dashboard")

        @app.route("/dashboard")
        def dashboard():
            if "user_id" not in session:
                return redirect("/")
            user = User.get_by_id(int(session["user_id"]))
            if user is None:
                del session["user_id"]
                return redirect("/")
            return render_template("/views/user/dashboard.html", user=user)

        @app.route("/logout")
        def logout():
            if "user_id" in session:
                del session["user_id"]
            return redirect("/")

        return self

    def create(self, form_data):
        data = {**form_data}
        data["email"] = data["email"].lower()

        if not User.validate_form_input(data):
            return redirect("/")

        session["user_id"] = self.model.create(data)
        flash("Success! Welcome to your new account", "success")
        return redirect("/dashboard")

    def update(self, form_data):
        if "user_id" not in session:
            return redirect("/")

        user = User.get_by_id(int(form_data["id"]))
        if user is None or session["user_id"] != int(form_data["id"]):
            return redirect("/")

        data = {**form_data}
        data["email"] = data["email"].lower()

        if not User.validate_form_input(data):
            return redirect(f"/users/{user.id}/edit", user=user)

        return super().update(data)

    def delete(self, id: int):
        if "user_id" not in session:
            return redirect("/")

        user = User.get_by_id(id)
        if user is None or session["user_id"] != user.id:
            return redirect("/dashboard")

        return super().delete(id)
