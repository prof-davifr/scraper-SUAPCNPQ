from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from core.background import run_automation_in_background, run_processing_in_background, get_current_state
from core.scraper import fetch_campus_list
import os
import logging

app = Flask(__name__, 
            template_folder='app/templates', 
            static_folder='app/static')

# Secret key for sessions
app.secret_key = os.urandom(24)

# Disable Flask/Werkzeug access logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/", methods=["GET", "POST"])
def index():
    # If already running, redirect to progress
    state = get_current_state()
    if state["is_running"]:
        return redirect(url_for("progress"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        try:
            # Discovery phase: get campuses
            campuses = fetch_campus_list(username, password)
            session["username"] = username
            session["password"] = password
            session["campuses"] = campuses
            return redirect(url_for("setup"))
        except Exception as e:
            flash(f"Erro ao conectar ao SUAP: {str(e)}", "error")
            return render_template("login.html")
        
    return render_template("login.html")

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if "username" not in session:
        return redirect(url_for("index"))

    state = get_current_state()
    if state["is_running"]:
        return redirect(url_for("progress"))

    if request.method == "POST":
        year_start = request.form.get("year_start")
        year_end = request.form.get("year_end")
        campus_filter = request.form.getlist("campus_filter") # Returns a list of values
        
        username = session.get("username")
        password = session.get("password")
        
        # Start background job
        run_automation_in_background(username, password, year_start, year_end, campus_filter)
            
        return redirect(url_for("progress"))
        
    campuses = session.get("campuses", [])
    return render_template("setup.html", campuses=campuses)

@app.route("/progress")
def progress():
    return render_template("progress.html")

@app.route("/api/status")
def status_api():
    return jsonify(get_current_state())

@app.route("/process-raw", methods=["POST"])
def process_raw():
    state = get_current_state()
    if state["is_running"]:
        flash("Já existe um processo em execução.", "error")
        return redirect(url_for("setup"))
    
    run_processing_in_background()
    return redirect(url_for("progress"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
