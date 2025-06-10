import uuid, requests, json, os
from datetime import datetime, UTC
from dotenv import load_dotenv
from src.core.prompt_parser import PromptParser

load_dotenv()

class WorkflowExecutor:
    def __init__(self):
        self.storage = {"$id": str(uuid.uuid4()),"$state": {},"$results": [],"$metadata": {"createdAt": datetime.now(UTC).isoformat() + "Z","startedAt": None,"executionTotal": 0}}
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000/task")
        self.prompt_parser = PromptParser()
    def _update_state(self, new_state):
        if new_state: self.storage["$state"].update(new_state)
    def _append_result(self, result):
        if result: self.storage["$results"].append(result)
    def _resolve_jsonpath(self, payload):
        resolved_payload = {}
        for key, value in payload.items():
            if isinstance(value, str):
                if value == "$state": resolved_payload[key] = self.storage["$state"]
                elif value.startswith("$state."):
                    state_key = value.split("$state.", 1)[1]
                    resolved_payload[key] = self.storage["$state"].get(state_key)
                else: resolved_payload[key] = value
            else: resolved_payload[key] = value
        return resolved_payload
    def execute_task(self, task_key, payload):
        resolved_payload = self._resolve_jsonpath(payload)
        url = f"{self.api_base_url}/{task_key}"
        print(f"\n---> Executing task: {task_key} <---")
        print(f"Payload: {json.dumps(resolved_payload, indent=2)}")
        try:
            response = requests.post(url, json=resolved_payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"FATAL: Error calling '{task_key}'.")
            if e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                try: print(f"Server Response: {json.dumps(e.response.json(), indent=2)}")
                except json.JSONDecodeError: print(f"Server Response (raw): {e.response.text}")
            else: print(f"Error: {e}")
            return False
        data = response.json()
        print(f"Response from {task_key}: {json.dumps(data, indent=2)}")
        self._update_state(data.get("state"))
        self._append_result(data.get("result"))
        self.storage["$metadata"]["executionTotal"] += 1
        if data.get("done"):
            print("\nWorkflow completed!")
            return False
        next_task = data.get("next")
        if next_task and next_task.get("key"):
            return self.execute_task(next_task["key"], next_task["payload"])
        return True
    def start_workflow(self, prompt):
        self.storage["$metadata"]["startedAt"] = datetime.now(UTC).isoformat() + "Z"
        print("Parsing prompt..."); parameters = self.prompt_parser.parse(prompt)
        if "error" in parameters: print(f"Error parsing prompt: {parameters['error']}"); return
        if not parameters.get("numberOfLeads"): parameters["numberOfLeads"] = 5
        print(f"Parsed parameters: {json.dumps(parameters, indent=2)}")
        return self.execute_task("input", parameters)
    def get_storage(self): return self.storage

def run_simulation():
    executor = WorkflowExecutor()
    prompt = "Cari 23 restaurant di Jakarta Selatan yang memiliki rating di atas 4.5, dengan harga terjangkau, dengan jumlah review minimal 30 buka dari jam 9 pagi sampai 10 malam"
    print("Starting workflow..."); executor.start_workflow(prompt)
    print("\n--- Final Central Storage ---"); storage = executor.get_storage()
    if storage.get("$results"):
        dict_results = [r for r in storage["$results"] if isinstance(r, dict)]
        dict_results.sort(key=lambda x: x.get("matchPercentage", 0), reverse=True)
        storage["$results"] = dict_results
    with open("central_storage_output.json", "w") as f: json.dump(storage, f, indent=2)
    print(f"Central Storage has been saved to central_storage_output.json")
    print(json.dumps(storage, indent=2))
if __name__ == "__main__": run_simulation()