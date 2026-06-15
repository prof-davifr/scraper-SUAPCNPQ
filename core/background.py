import threading
from core.scraper import login_and_scrape
from core.processor import process_all_raw_data
from utils.logger import log_msg
import time

# Global state to share between the background thread and Flask
state_lock = threading.Lock()
task_state = {
    "is_running": False,
    "current_campus": None,
    "status": "Inativo",
    "status_start_time": 0.0,
    "files_downloaded": 0,
    "total_campuses": 0,
    "error": None,
    "mode": "scrape"  # "scrape" or "process"
}

def update_state(status, current_campus=None, error=None):
    with state_lock:
        if status and status != task_state.get("status"):
            task_state["status"] = status
            task_state["status_start_time"] = time.time()
            
        if current_campus:
            task_state["current_campus"] = current_campus
        if error:
            task_state["error"] = error
            
        if status == "Concluído":
            task_state["files_downloaded"] += 1
            
        if status == "Processo finalizado" or "falhou" in status.lower():
            if status != "Concluído" and "falhou" not in status.lower():
                 pass # Still running if it's just completed one campus
            else:
                 task_state["is_running"] = False

def run_automation_in_background(username, password, year_start, year_end, campus_filter=None):
    # Initialize state
    with state_lock:
        task_state["is_running"] = True
        task_state["current_campus"] = None
        task_state["status"] = "Inicializando"
        task_state["files_downloaded"] = 0
        task_state["error"] = None
        task_state["mode"] = "scrape"

    def target():
        try:
            log_msg("Iniciando thread de automação em segundo plano.")
            login_and_scrape(username, password, year_start, year_end, 
                             campus_filter=campus_filter, 
                             state_callback=update_state)
        except Exception as e:
            msg = f"A automação lançou uma exceção: {str(e)}"
            log_msg(msg)
            update_state("Erro", error=str(e))
        finally:
            with state_lock:
                task_state["is_running"] = False
            log_msg("Thread em segundo plano finalizada.")

    t = threading.Thread(target=target, daemon=True)
    t.start()
    return True

def run_processing_in_background():
    # Initialize state
    with state_lock:
        task_state["is_running"] = True
        task_state["current_campus"] = None
        task_state["status"] = "Inicializando processamento"
        task_state["files_downloaded"] = 0
        task_state["error"] = None
        task_state["mode"] = "process"

    def target():
        try:
            log_msg("Iniciando processamento de dados brutos em segundo plano.")
            from core.processor import process_all_raw_data
            process_all_raw_data("data/raw", "data/processed", state_callback=update_state)
        except Exception as e:
            msg = f"O processamento lançou uma exceção: {str(e)}"
            log_msg(msg)
            update_state("Erro", error=str(e))
        finally:
            with state_lock:
                task_state["is_running"] = False
            log_msg("Thread de processamento finalizada.")

    t = threading.Thread(target=target, daemon=True)
    t.start()
    return True

def get_current_state():
    with state_lock:
        return dict(task_state)
