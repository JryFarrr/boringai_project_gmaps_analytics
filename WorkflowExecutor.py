import uuid, requests, json, os, logging
from datetime import datetime, UTC
from dotenv import load_dotenv
from src.core.prompt_parser import PromptParser

load_dotenv()

class WorkflowExecutor:
    def __init__(self):
        self.storage = {"$id": str(uuid.uuid4()),"$state": {},"$results": [],"$metadata": {"createdAt": datetime.now(UTC).isoformat() + "Z","startedAt": None,"executionTotal": 0}}
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000/task")
        self.prompt_parser = PromptParser()

        # --- PENAMBAHAN LOGGING ---
        # Mengatur logger untuk menyimpan semua panggilan API ke file.
        self.logger = logging.getLogger("WorkflowAPI")
        self.logger.setLevel(logging.INFO)
        # 'w' untuk write mode, log akan di-overwrite setiap kali script dijalankan.
        # Ganti ke 'a' (append) jika Anda ingin menyimpan riwayat dari beberapa eksekusi.
        file_handler = logging.FileHandler("workflow_api_calls.log", mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        # Menghindari duplikasi handler jika __init__ dipanggil lebih dari sekali
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
        # --- AKHIR PENAMBAHAN LOGGING ---

    def _update_state(self, new_state):
        """Menggabungkan (merge) state parsial dari respons API ke dalam state utama."""
        if new_state:
            self.storage["$state"].update(new_state)

    def _append_result(self, result):
        """Menambahkan hasil dari task 'analyze' ke dalam daftar results."""
        if result:
            self.storage["$results"].append(result)

    def _get_nested_val(self, data_dict, key_path):
        """Helper untuk mendapatkan nilai dari path bersarang (e.g., 'constraints.min_rating')."""
        keys = key_path.split('.')
        val = data_dict
        try:
            for key in keys:
                val = val[key]
            return val
        except (KeyError, TypeError, AttributeError):
            return None

    def _resolve_jsonpath(self, payload):
        """Mengganti referensi '$state' dalam payload dengan nilai aktual dari state utama."""
        resolved_payload = {}
        if not isinstance(payload, dict):
            return payload

        for key, value in payload.items():
            if isinstance(value, str):
                if value == "$state":
                    resolved_payload[key] = self.storage["$state"]
                elif value.startswith("$state."):
                    path = value.split("$state.", 1)[1]
                    resolved_payload[key] = self._get_nested_val(self.storage["$state"], path)
                else:
                    resolved_payload[key] = value
            elif isinstance(value, dict):
                resolved_payload[key] = self._resolve_jsonpath(value)
            else:
                resolved_payload[key] = value
        return resolved_payload

    def execute_task(self, task_key, payload):
        """Mengeksekusi satu task API, menangani respons, dan mencatatnya ke log."""
        resolved_payload = self._resolve_jsonpath(payload)

        if isinstance(resolved_payload, dict) and 'state' in resolved_payload and len(resolved_payload) == 1:
            final_payload = resolved_payload['state']
        else:
            final_payload = resolved_payload
        
        url = f"{self.api_base_url}/{task_key}"
        
        print(f"\n---> Executing task: {task_key} <---")
        # Mencatat request ke file log
        self.logger.info(f"REQUEST to [{task_key}]\nPAYLOAD:\n{json.dumps(final_payload, indent=2)}")

        try:
            response = requests.post(url, json=final_payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            error_msg = f"API call to [{task_key}] FAILED: {e}"
            print(f"FATAL: Error calling '{task_key}'.")
            if e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                try:
                    server_error = e.response.json()
                    print(f"Server Response: {json.dumps(server_error, indent=2)}")
                    error_msg += f"\nSERVER RESPONSE:\n{json.dumps(server_error, indent=2)}"
                except json.JSONDecodeError:
                    print(f"Server Response (raw): {e.response.text}")
                    error_msg += f"\nSERVER RESPONSE (RAW):\n{e.response.text}"
            else:
                print(f"Error: {e}")
            # Mencatat error ke file log
            self.logger.error(error_msg)
            return False

        data = response.json()
        # Mencatat response ke file log
        self.logger.info(f"RESPONSE from [{task_key}]\nBODY:\n{json.dumps(data, indent=2)}")
        
        self._update_state(data.get("state"))
        self._append_result(data.get("result"))
        self.storage["$metadata"]["executionTotal"] += 1
        
        if data.get("done"):
            print("\nWorkflow completed!")
            return False
            
        next_task = data.get("next")
        if next_task and next_task.get("key"):
            return self.execute_task(next_task["key"], next_task["payload"])
            
        print("\nWorkflow ended without a 'next' task or 'done' flag.")
        return False

    def start_workflow(self, prompt):
        """Memulai alur kerja dari sebuah prompt."""
        self.storage["$metadata"]["startedAt"] = datetime.now(UTC).isoformat() + "Z"
        
        print("Parsing prompt...")
        parameters = self.prompt_parser.parse(prompt)
        if "error" in parameters:
            print(f"Error parsing prompt: {parameters['error']}")
            return
            
        if not parameters.get("numberOfLeads"):
            parameters["numberOfLeads"] = 5
        print(f"Parsed parameters: {json.dumps(parameters, indent=2)}")
        
        self.execute_task("input", parameters)

    def get_storage(self):
        return self.storage

def run_simulation():
    """Menjalankan simulasi alur kerja dari awal hingga akhir."""
    executor = WorkflowExecutor()
    prompt = "Cari 10 restaurant dengan rating minimal 4.5 di daerah lembang bandung"
    
    print("Starting workflow...")
    executor.start_workflow(prompt)
    
    print("\n--- Final Central Storage ---")
    storage = executor.get_storage()
    if storage.get("$results"):
        dict_results = [r for r in storage["$results"] if isinstance(r, dict)]
        dict_results.sort(key=lambda x: x.get("matchPercentage", 0), reverse=True)
        storage["$results"] = dict_results
        
    output_filename = "central_storage_output.json"
    with open(output_filename, "w") as f:
        json.dump(storage, f, indent=2)
        
    print(f"Central Storage has been saved to {output_filename}")
    print("API call logs have been saved to workflow_api_calls.log")

if __name__ == "__main__":
    run_simulation()