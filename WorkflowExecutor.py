import uuid
from datetime import datetime, UTC
import requests
import json
import os
from dotenv import load_dotenv
from src.services.prompt_parser import parse_prompt

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
                "createdAt": datetime.now(UTC).isoformat() + "Z",
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
        # Enrich payload dengan parameter untuk task analyze
        if task_key == "analyze":
            enriched_payload = payload.copy()
            enriched_payload["constraints"] = {}
            
            constraint_keys = ["min_rating", "min_reviews", "max_reviews", "price_range", 
                               "business_hours", "keywords"]
            
            for key in constraint_keys:
                if key in self.storage["$state"] and self.storage["$state"][key] is not None:
                    enriched_payload["constraints"][key] = self.storage["$state"][key]
                    print(f"Added constraint from state: {key} = {self.storage['$state'][key]}")
            
            payload = enriched_payload
            print(f"Analyze payload after adding constraints from state: {json.dumps(payload, indent=2)}")
            
        # For control task, prepare complete payload with all required fields
        elif task_key == "control":
            # Ensure all required fields are included
            complete_payload = {
                "leadCount": self.storage["$state"].get("leadCount", 0),
                "numberOfLeads": self.storage["$state"].get("numberOfLeads", 0),
                "remainingPlaceIds": self.storage["$state"].get("remainingPlaceIds", []),
                "searchOffset": self.storage["$state"].get("searchOffset", 0)
            }
            
            # Update with any values from the original payload
            complete_payload.update(payload)
            payload = complete_payload
            print(f"Control payload: {json.dumps(payload, indent=2)}")
    
        # URL endpoint from environment variable
        url = f"{self.api_base_url}/{task_key}"
        print(f"Executing task: {task_key}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Lempar error jika status bukan 200
        except requests.RequestException as e:
            print(f"Error calling {task_key}: {str(e)}")
            return False
    
        data = response.json()
        print(f"Response from {task_key}: {json.dumps(data, indent=2)}")
    
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

    def start_workflow(self, parameters):
        """Memulai workflow dengan input awal dari pengguna dan parameter tambahan"""
        self.storage["$metadata"]["startedAt"] = datetime.now(UTC).isoformat() + "Z"
            
        # Save all parameters including constraints to the instance
        self.parameters = parameters
    
        return self.execute_task("input", parameters)

    def get_storage(self):
        """Mengembalikan isi Central Storage untuk inspeksi"""
        return self.storage

# Fungsi untuk menjalankan simulasi
def run_simulation():
    executor = WorkflowExecutor()
    
    prompt = "Temukan barbershop yang potongannya bagus di surabaya"
    # prompt nanti diparsing untuk menentukan businessType, location, dan numberOfLeads
    # prompt juga diparsing untuk contraints pada match percentage
    # untuk match percentage disimpan pada instance, dan hanya digunakan di analyze
    
    parameters = parse_prompt(prompt)
    
    # Check if parsing returned an error response
    if "error" in parameters and parameters.get("done", False):
        print(f"Error: {parameters['error']}")
        print("Cannot proceed with workflow execution due to parsing failure.")
        return
    
    # If numberOfLeads is empty, set it to 1; otherwise keep the original value
    if parameters["numberOfLeads"] == "":
        parameters["numberOfLeads"] = 1
    
    # Make sure max_reviews is properly handled
    if "max_reviews" not in parameters:
        parameters["max_reviews"] = None

    print(f"Full parameters: {parameters}")

    # Jalankan workflow with parameters
    print("Starting workflow...")
    executor.start_workflow(parameters)
    
    # Tampilkan Central Storage setelah selesai
    print("\nFinal Central Storage:")
    storage = executor.get_storage()
    
    # Sort $results by fitScore in descending order
    storage["$results"].sort(key=lambda x: x.get("matchPercentage", 0), reverse=True)
    
    # Replace empty fields with None in $results
    for result in storage["$results"]:
        for key, value in result.items():
            if value == "":
                result[key] = None
    
    print(json.dumps(storage, indent=2))
    
    # Save the Central Storage to a JSON file
    output_file = "central_storage_output.json"
    with open(output_file, "w") as f:
        json.dump(storage, f, indent=2)
    print(f"Central Storage has been saved to {output_file}")

if __name__ == "__main__":
    run_simulation()