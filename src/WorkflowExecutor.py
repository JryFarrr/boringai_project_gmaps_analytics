import uuid
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WorkflowExecutor:
    def __init__(self):
        # Inisialisasi Central Storage Schema
        self.storage = {
            "$id": str(uuid.uuid4()),  # ID unik untuk sesi
            "$state": {},              # State sementara untuk workflow
            "$results": [],            # Hasil akumulasi dari tugas
            "$metadata": {             # Metadata opsional
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "startedAt": None,
                "executionTotal": 0
            }
        }
        # Get API base URL from environment variable
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000/task")

    def update_state(self, new_state):
        """Memperbarui $state dengan data baru menggunakan non-destructive patching"""
        if new_state:
            self.storage["$state"].update(new_state)

    def append_result(self, result):
        """Menambahkan hasil tugas ke $results"""
        if result:
            self.storage["$results"].append(result)

    def resolve_jsonpath(self, payload):
        """Mengganti JSONPath seperti $state.key dengan nilai dari $state"""
        resolved_payload = {}
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("$state."):
                state_key = value.split("$state.")[1]
                resolved_payload[key] = self.storage["$state"].get(state_key)
            else:
                resolved_payload[key] = value
        return resolved_payload

    def execute_task(self, task_key, payload):
        """Memanggil endpoint tugas dan memproses respons"""
        # URL endpoint from environment variable
        url = f"{self.api_base_url}/{task_key}"
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Lempar error jika status bukan 200
        except requests.RequestException as e:
            print(f"Error calling {task_key}: {str(e)}")
            return False

        data = response.json()

        # Proses respons sesuai unified contract
        self.update_state(data.get("state"))
        self.append_result(data.get("result"))
        self.storage["$metadata"]["executionTotal"] += 1

        # Cek apakah workflow selesai
        if data.get("done"):
            print("Workflow completed!")
            return False

        # Lanjutkan ke tugas berikutnya jika ada
        next_task = data.get("next")
        if next_task:
            resolved_payload = self.resolve_jsonpath(next_task["payload"])
            return self.execute_task(next_task["key"], resolved_payload)

        return True

    def start_workflow(self, initial_input):
        """Memulai workflow dengan input awal dari pengguna"""
        self.storage["$metadata"]["startedAt"] = datetime.utcnow().isoformat() + "Z"
        return self.execute_task("input", initial_input)

    def get_storage(self):
        """Mengembalikan isi Central Storage untuk inspeksi"""
        return self.storage

# Fungsi untuk menjalankan simulasi
def run_simulation():
    executor = WorkflowExecutor()
    
    # Input awal dari pengguna
    initial_input = {
        "businessType": "Coffee Shop",
        "location": "New York",
        "numberOfLeads": 10
    }
    
    # Jalankan workflow
    print("Starting workflow...")
    executor.start_workflow(initial_input)
    
    # Tampilkan Central Storage setelah selesai
    print("\nFinal Central Storage:")
    print(json.dumps(executor.get_storage(), indent=2))

if __name__ == "__main__":
    run_simulation()