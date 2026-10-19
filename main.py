from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from core.background import run_automation_in_background, run_processing_in_background, get_current_state
from core.scraper import fetch_campus_list
import os
import secrets
import logging

app = Flask(__name__, 
            template_folder='app/templates', 
            static_folder='app/static')

# Secret key for sessions
app.secret_key = os.urandom(24)

# A sessão do Flask é um cookie assinado, não criptografado: quem tem o cookie
# lê o conteúdo. Por isso a senha do SUAP fica só na memória deste processo e o
# cookie leva apenas uma chave aleatória. Some quando o servidor reinicia, como
# a própria sessão (a secret_key também é nova a cada início).
_credenciais = {}


def guardar_credencial(username, password):
    """Guarda (usuário, senha) na memória e devolve a chave que vai no cookie."""
    chave = secrets.token_urlsafe(32)
    _credenciais[chave] = (username, password)
    return chave


def credencial_da_sessao():
    """(usuário, senha) da sessão atual, ou None se não houver login válido."""
    chave = session.get("credencial")
    return _credenciais.get(chave) if chave else None

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
            _credenciais.pop(session.get("credencial"), None)
            session.clear()
            session["username"] = username
            session["credencial"] = guardar_credencial(username, password)
            session["campuses"] = campuses
            return redirect(url_for("setup"))
        except Exception as e:
            flash(f"Erro ao conectar ao SUAP: {str(e)}", "error")
            return render_template("login.html")
        
    return render_template("login.html")

@app.route("/setup", methods=["GET", "POST"])
def setup():
    credencial = credencial_da_sessao()
    if credencial is None:
        return redirect(url_for("index"))

    state = get_current_state()
    if state["is_running"]:
        return redirect(url_for("progress"))

    if request.method == "POST":
        year_start = request.form.get("year_start")
        year_end = request.form.get("year_end")
        campus_filter = request.form.getlist("campus_filter") # Returns a list of values
        
        username, password = credencial
        
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
