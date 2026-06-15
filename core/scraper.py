import os
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from utils.logger import log_msg
from core.processor import merge_production_data

# We use a 120-minute timeout for report generation/download, since it can take up to 2 hours.
LONG_TIMEOUT = 120 * 60 * 1000  

def setup_dirs():
    raw_path = Path("data/raw")
    processed_path = Path("data/processed")
    raw_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    return str(raw_path.resolve()), str(processed_path.resolve())

def fetch_campus_list(username, password):
    """
    Realiza o login e extrai a lista de campi disponíveis.
    Retorna uma lista de dicionários com 'value', 'sigla' e 'text'.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(60 * 1000)

        # Login
        page.goto("https://suap.ifba.edu.br/accounts/login/")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")

        if "login" in page.url:
            browser.close()
            raise Exception("Falha no login. Verifique suas credenciais.")

        # Ir para página de relatório
        target_url = "https://suap.ifba.edu.br/cnpq/producao_por_campus_detalhado/"
        page.goto(target_url)
        page.wait_for_load_state("networkidle")

        # Buscar select de campi
        campus_select = page.locator("select[name*='campus'], select[id*='campus']").first
        if not campus_select.is_visible():
             campus_select = page.get_by_label(re.compile(r"campus", re.IGNORECASE)).first

        options = campus_select.locator("option").all()
        campuses = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val and val != "":
                sigla_match = re.search(r'\(([^)]+)\)', text)
                sigla = sigla_match.group(1) if sigla_match else text
                campuses.append({"value": val, "sigla": sigla, "text": text})

        browser.close()
        return campuses

def login_and_scrape(username, password, year_start, year_end, campus_filter=None, state_callback=None):
    """
    state_callback: function that accepts a dict to update the flask app's state.
    """
    def set_state(status, current_campus=None):
        if state_callback:
            state_callback(status, current_campus)
        log_msg(f"STATUS: {status} | CAMPUS: {current_campus}")

    
    with sync_playwright() as p:
        set_state("Iniciando Navegador")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(LONG_TIMEOUT) # Use long timeout (120 min) as default

        # 1. Login
        set_state("Fazendo Login")
        page.goto("https://suap.ifba.edu.br/accounts/login/")
        
        # Standard SUAP login fields (Django)
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("input[type='submit']")
        
        # Verify login success (look for login error or check URL)
        # We'll just wait for the page to finish navigating
        page.wait_for_load_state("networkidle")
        if "login" in page.url:
            set_state("Login falhou")
            browser.close()
            raise Exception("Login falhou. Verifique suas credenciais.")

        set_state("Login realizado com sucesso")

        # 2. Go to target page
        target_url = "https://suap.ifba.edu.br/cnpq/producao_por_campus_detalhado/"
        page.goto(target_url)
        page.wait_for_load_state("networkidle")

        # 3. Get list of campuses
        set_state("Buscando lista de campi")
        
        # Try to find the campus select element. We use a somewhat generic locator
        # assuming the select name contains 'campus' or id contains 'campus'
        campus_select = page.locator("select[name*='campus'], select[id*='campus']").first
        
        if not campus_select.is_visible():
            # Try finding the select next to a label
            campus_select = page.get_by_label(re.compile(r"campus", re.IGNORECASE)).first

        options = campus_select.locator("option").all()
        
        campuses = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val: # Skip empty options like "Select..."
                # Extract SIGLA if possible e.g. "Salvador (SSA)" -> "SSA"
                sigla_match = re.search(r'\(([^)]+)\)', text)
                sigla = sigla_match.group(1) if sigla_match else text
                # We need the value to submit the form, and sigla for renaming
                campuses.append({"value": val, "sigla": sigla, "text": text})

        log_msg(f"Encontrados {len(campuses)} campi no sistema.")

        # Filter by campus if requested
        if campus_filter:
            if isinstance(campus_filter, list):
                # Multiple campuses selected via checkboxes
                campuses = [c for c in campuses if c["value"] in campus_filter]
                log_msg(f"Filtro de múltipla escolha aplicado: {len(campuses)} campi selecionados.")
            else:
                # Single campus selected via string/manual filter
                target_val = campus_filter.strip()
                filtered = [c for c in campuses if c["value"] == target_val]
                
                if not filtered:
                    target_upper = target_val.upper()
                    filtered = [c for c in campuses if target_upper in c["sigla"].upper() or target_upper in c["text"].upper()]
                
                campuses = filtered
                log_msg(f"Filtro aplicado '{target_val}': {len(campuses)} campi restantes.")
            
            if not campuses:
                log_msg(f"Aviso: Nenhum campus encontrado com os critérios fornecidos.")

        # 4. Iterate and download
        # Adding a retry wrapper
        
        for campus_info in campuses:
            campus_val = campus_info["value"]
            campus_sigla = campus_info["sigla"]
            
            success = False
            for attempt in range(1, 4):
                try:
                    set_state(f"Processando (Tentativa {attempt})", campus_sigla)
                    
                    # Refresh target page to have a clean form
                    page.goto(target_url)
                    page.wait_for_load_state("networkidle")
                    
                    # Fill form
                    campus_select = page.locator("select[name*='campus'], select[id*='campus']").first
                    campus_select.select_option(value=campus_val)
                    
                    # Fill years
                    try:
                        year_start_select = page.locator("select[name='inicio_periodo']").first
                        if not year_start_select.is_visible(timeout=3000):
                            year_start_select = page.get_by_label(re.compile(r"in[ií]cio", re.IGNORECASE)).first
                        year_start_select.select_option(label=str(year_start))
                    except Exception as e:
                        log_msg(f"Aviso: Não foi possível selecionar o ano inicial '{year_start}'. {e}")
                    
                    try:
                        year_end_select = page.locator("select[name='fim_periodo']").first
                        if not year_end_select.is_visible(timeout=3000):
                            year_end_select = page.get_by_label(re.compile(r"fim|final", re.IGNORECASE)).first
                        year_end_select.select_option(label=str(year_end))
                    except Exception as e:
                        log_msg(f"Aviso: Não foi possível selecionar o ano final '{year_end}'. {e}")
                    
                    # Submit and wait for table/results
                    set_state("Gerando relatório", campus_sigla)
                    submit_btn = page.locator("input[name='producaocampusdetalhado_form'][type='submit']").first
                    submit_btn.click()
                    
                    # This can take minutes
                    # We wait for the results table or some indicator
                    page.wait_for_selector("table", timeout=LONG_TIMEOUT)
                    
                    # Now download XLS
                    set_state("Aguardando geração do XLS", campus_sigla)
                    
                    # Expect download event
                    with page.expect_download(timeout=LONG_TIMEOUT) as download_info:
                        # Click the exact "Exportar para XLS" link
                        xls_btn = page.get_by_role("link", name="Exportar para XLS").first
                        if not xls_btn.is_visible(timeout=5000):
                            # Fallback just in case
                            xls_btn = page.locator("a:has-text('Exportar para XLS')").first
                        xls_btn.click()
                    
                    download = download_info.value
                    
                    # Rename file
                    set_state("Baixando arquivo", campus_sigla)
                    
                    filename = f"{campus_sigla}-{year_start}-{year_end}.xls"
                    # Clean filename of unsafe characters
                    filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
                    
                    raw_dir, processed_dir = setup_dirs()
                    filepath = os.path.join(raw_dir, filename)
                    download.save_as(filepath)
                    
                    log_msg(f"Download concluído: {filepath}")
                    
                    # Merge with existing data in processed directory
                    merge_production_data(filepath, campus_sigla, processed_dir)
                    
                    set_state("Concluído", campus_sigla)
                    success = True
                    break # Break out of retries on success
                    
                except Exception as e:
                    log_msg(f"Erro ao processar {campus_sigla} na tentativa {attempt}: {str(e)}")
                    time.sleep(2) # brief pause before retry
                    
            if not success:
                log_msg(f"Falha ao processar o campus {campus_sigla} após 3 tentativas.")
        
        set_state("Processo finalizado")
        browser.close()
