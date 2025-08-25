from flask import render_template, request, redirect, url_for, flash
from extensions import db
from models import User
from routes import auth_bp
from flask_login import login_user, logout_user, login_required, current_user

@auth_bp.get("/register")
def register_form():
    return render_template("register.html")

@auth_bp.post("/register")
def register_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    # Basic validation
    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("auth.register_form"))
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        flash("That email is already registered.", "error")
        return redirect(url_for("auth.register_form"))
    # Create and save the new user
    u = User(email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    # Notify user of success
    flash("Account created. You can now log in.", "success")
    return redirect(url_for("auth.register_form"))

@auth_bp.get("/login")
def login_form():
    return render_template("login.html")

@auth_bp.post("/login")
def login_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login_form"))

    login_user(user)
    flash("Welcome back!", "success")
    return redirect(url_for("jobs.dashboard"))

@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login_form"))