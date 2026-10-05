"""Mapa sigla do SUAP → código do dashboard e filtro do --sincronizar.

Sem rede e sem navegador: só core/siglas.py e o merge_production_data sobre
uma planilha mínima, sem dado pessoal, criada no diretório temporário.
"""
import pandas as pd
import pytest

import core.processor as processor
import core.siglas as siglas
from core.siglas import (CODIGOS_DASHBOARD, SUAP_PARA_DASHBOARD,
                         codigo_dashboard, separar_para_sincronizar)


@pytest.fixture
def avisos(monkeypatch):
    """Captura o log em vez de gravar em logs/run.log."""
    msgs = []
    monkeypatch.setattr(siglas, "log_msg", msgs.append)
    monkeypatch.setattr(processor, "log_msg", msgs.append)
    return msgs


def test_mapa_aponta_para_codigos_do_dashboard():
    assert SUAP_PARA_DASHBOARD == {"FSA": "FS", "PAF": "PA", "VDC": "VC"}
    assert set(SUAP_PARA_DASHBOARD.values()) <= CODIGOS_DASHBOARD
    # Sigla antiga não pode ser, ao mesmo tempo, código aceito pelo dashboard.
    assert not set(SUAP_PARA_DASHBOARD) & CODIGOS_DASHBOARD


@pytest.mark.parametrize("suap, dashboard", [
    ("FSA", "FS"), ("PAF", "PA"), ("VDC", "VC"),
    ("FS", "FS"), ("SSA", "SSA"), ("ITA", "ITA"), ("IFBA", "IFBA"),
])
def test_codigo_dashboard_sem_aviso(avisos, suap, dashboard):
    assert codigo_dashboard(suap) == dashboard
    assert avisos == []


def test_sigla_desconhecida_passa_com_aviso(avisos):
    assert codigo_dashboard("CAJ") == "CAJ"
    assert len(avisos) == 1
    assert "AVISO" in avisos[0] and "'CAJ'" in avisos[0]


def test_sincronizar_deixa_de_fora_siglas_antigas_e_desconhecidas(tmp_path):
    mestres = [tmp_path / f"{s}.xlsx" for s in ("FS", "FSA", "PAF", "VC", "VDC", "REI", "CAJ")]
    copiar, ignorados = separar_para_sincronizar(mestres)

    assert [m.stem for m in copiar] == ["FS", "VC", "REI"]
    motivos = {m.stem: motivo for m, motivo in ignorados}
    assert set(motivos) == {"FSA", "PAF", "VDC", "CAJ"}
    assert "FS.xlsx" in motivos["FSA"]
    assert "desconhecida" in motivos["CAJ"]


def test_merge_grava_sigla_renomeada_no_mestre_antigo(tmp_path, avisos):
    processed = tmp_path / "processed"
    processed.mkdir()
    aba = "Produções Técnicas"
    colunas = ["#", "Servidor", "Publicação", "Ano", "Tipo"]

    with pd.ExcelWriter(processed / "FS.xlsx", engine="openpyxl") as w:
        pd.DataFrame([[1, "S1", "Software A", 2023, "Software"]], columns=colunas) \
            .to_excel(w, sheet_name=aba, index=False)
    novo = tmp_path / "FSA-2024-2024.xlsx"
    with pd.ExcelWriter(novo, engine="openpyxl") as w:
        pd.DataFrame([[1, "S2", "Software B", 2024, "Software"]], columns=colunas) \
            .to_excel(w, sheet_name=aba, index=False)

    destino = processor.merge_production_data(str(novo), "FSA", str(processed))

    assert destino == str(processed / "FS.xlsx")
    assert not (processed / "FSA.xlsx").exists()
    df = pd.read_excel(destino, sheet_name=aba)
    assert sorted(df["Publicação"]) == ["Software A", "Software B"]
