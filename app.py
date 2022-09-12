import os

import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///vertretungsplan.db")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        student = request.form.get("student")
        teacher = request.form.get("teacher")
        klassenID = request.form.get("klassen_id")
        if teacher and student:
            return render_template("/register.html")
        elif teacher:
            db.execute("INSERT INTO Teachers (name, password) VALUES (?, ?)", name, generate_password_hash(password))
            id = db.execute("SELECT ID FROM Teachers where name = ?", name)
            return render_template("/registered.html", data=id)
        elif student:
            db.execute("INSERT INTO Students (name, password, klassenID) VALUES (?, ?, ?)", name, generate_password_hash(password), klassenID)
            id = db.execute("SELECT ID FROM Students where name = ?", name)
            return render_template("/registered.html", data=id)
        else:
            return render_template("/register.html")
    else:
        return render_template("/register.html")

@app.route("/registered", methods=["POST", "GET"])
def registered():
    if request.method == "POST":
        return render_template("/register.html")
    else:
        return render_template("/registered.html")

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        student = request.form.get("student")
        teacher = request.form.get("teacher")
        if student and teacher:
            return redirect("/")
        elif student:
            return redirect("/student_login")
        elif teacher:
            return redirect("/teacher_login")
        else:
            return redirect("/")
    else:
        return render_template("/home.html")

@app.route("/student_login", methods=["POST", "GET"])
def student_login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("student_id"):
            return render_template("/student_login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("/student_login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM Students WHERE ID = ?", request.form.get("student_id"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template("/student_login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["ID"]

        return render_template("/student_vertretungsplan.html", data=["student"])
    else:
        return render_template("/student_login.html")

@app.route("/teacher_login", methods=["POST", "GET"])
def teacher_login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("teacher_id"):
            return render_template("/teacher_login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("/teacher_login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM Teachers WHERE ID = ?", request.form.get("teacher_id"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template("/teacher_login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["ID"]

        return render_template("/teacher_vertretungsplan.html", data=["teacher"])
    else:
        return render_template("/teacher_login.html")

@app.route("/teacher_vertretungsplan", methods=["POST", "GET"])
@login_required
def teacher_vertretungsplan():
    data = db.execute("SELECT * FROM Vertretung WHERE lehrerID = ?", session["user_id"])
    return render_template("/teacher_vertretungsplan.html", data=["teacher", data])

@app.route("/student_vertretungsplan", methods=["POST", "GET"])
@login_required
def student_vertretungsplan():
    klassenID = db.execute("SELECT klassenID FROM Students WHERE ID=?", session["user_id"])
    data = db.execute("SELECT * FROM Vertretung WHERE klassenID = ?", klassenID[0]["klassenID"])
    return render_template("/student_vertretungsplan.html", data=["student", data])

@app.route("/teacher_ill", methods=["POST", "GET"])
@login_required
def teacher_ill():
    monday = request.form.get("monday")
    if monday:
        stunden = db.execute("SELECT mo1, mo2, mo3, mo4, mo5, mo6 FROM Teachers WHERE ID = ?", session["user_id"])[0]
        for stunde in stunden:
            if stunde == "mo1" or stunde == "mo6":
                klasse_fach = stunden[stunde].split("/")
                db.execute("INSERT INTO Vertretung (lehrerID, klassenID, zeit, fach) VALUES (?,?,?,?)", 1, klasse_fach[0], stunde, klasse_fach[1])
            else:
                klasse_fach = stunden[stunde].split("/")
                verfügbare_lehrer = db.execute("SELECT ID FROM Teachers WHERE fach = ?", klasse_fach[1])
                if verfügbare_lehrer:
                    db.execute("INSERT INTO Vertretung (lehrerID, klasse, zeit, fach) VALUES (?,?,?,?)", verfügbare_lehrer[0], klasse_fach[0], stunde, klasse_fach[1])
                else:
                    db.execute("INSERT INTO Vertretung (lehrerID, klassenID, zeit, fach) VALUES (?,?,?,?)", 0, klasse_fach[0], stunde, klasse_fach[1])

    return render_template("/teacher_ill.html", data=["teacher"])

@app.route("/student_ill", methods=["POST", "GET"])
@login_required
def student_ill():
    # TODO
    return render_template("/student_ill.html", data=["student"])


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")