"""A senha do SUAP não pode ir no cookie de sessão do Flask.

Sem rede e sem navegador: fetch_campus_list e o worker de segundo plano são
trocados por dublês. A credencial é inventada; nenhum login real acontece.
"""
import pytest

import main

USUARIO = "0000000"
SENHA = "senha-de-teste-nao-real"
CAMPI = [{"value": "1", "sigla": "SSA", "text": "Campus Salvador (SSA)"}]


@pytest.fixture
def cliente(monkeypatch):
    chamadas = {"login": [], "worker": []}

    def fetch(username, password):
        chamadas["login"].append((username, password))
        return CAMPI

    def worker(*args):
        chamadas["worker"].append(args)
        return True

    monkeypatch.setattr(main, "fetch_campus_list", fetch)
    monkeypatch.setattr(main, "run_automation_in_background", worker)
    monkeypatch.setattr(main, "get_current_state", lambda: {"is_running": False})
    monkeypatch.setattr(main, "_credenciais", {})
    main.app.config["TESTING"] = True
    with main.app.test_client() as c:
        c.chamadas = chamadas
        yield c


def conteudo_do_cookie(cliente):
    """Decodifica o cookie de sessão como faria quem o interceptasse."""
    cookie = cliente.get_cookie(main.app.config["SESSION_COOKIE_NAME"])
    assert cookie is not None
    serializer = main.app.session_interface.get_signing_serializer(main.app)
    return cookie.value, serializer.loads(cookie.value)


def entrar(cliente):
    return cliente.post("/", data={"username": USUARIO, "password": SENHA})


def test_login_nao_poe_a_senha_no_cookie(cliente):
    resp = entrar(cliente)
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/setup")
    assert cliente.chamadas["login"] == [(USUARIO, SENHA)]

    bruto, sessao = conteudo_do_cookie(cliente)
    assert "password" not in sessao
    assert SENHA not in repr(sessao)
    assert SENHA not in bruto
    assert sessao["username"] == USUARIO
    assert sessao["credencial"] in main._credenciais


def test_setup_entrega_a_credencial_ao_worker(cliente):
    entrar(cliente)
    resp = cliente.post("/setup", data={"year_start": "2024", "year_end": "2026",
                                        "campus_filter": ["1"]})
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/progress")
    assert cliente.chamadas["worker"] == [(USUARIO, SENHA, "2024", "2026", ["1"])]


def test_setup_sem_login_volta_para_o_inicio(cliente):
    resp = cliente.get("/setup")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/")


def test_chave_desconhecida_nao_abre_o_setup(cliente):
    """Cookie de antes de um reinício: a chave não existe mais na memória."""
    entrar(cliente)
    main._credenciais.clear()
    resp = cliente.get("/setup")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/")


def test_novo_login_descarta_a_credencial_anterior(cliente):
    entrar(cliente)
    _, primeira = conteudo_do_cookie(cliente)
    entrar(cliente)
    _, segunda = conteudo_do_cookie(cliente)
    assert primeira["credencial"] != segunda["credencial"]
    assert list(main._credenciais) == [segunda["credencial"]]
