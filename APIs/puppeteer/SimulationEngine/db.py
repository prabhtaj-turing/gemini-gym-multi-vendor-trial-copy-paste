import json


DB = {
  "contexts": {
    "default": {
      "active_page": None,
      "pages": {}
    }
  },
  "active_context": "default",
  "logs": [],
  "screenshots": [],
  "script_results": [],
  "page_history": []
}

def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath = 'DBs/PuppeteerDefaultDB.json', error_config_path: str = "./error_config.json", error_definitions_path: str = "./error_definitions.json") -> object:
    global DB
    # with open(filepath, "r") as f:
    #     state = json.load(f)
    state = {
              "contexts": {
                "default": {
                  "active_page": None,
                  "pages": {}
                }
              },
              "active_context": "default",
              "logs": [],
              "screenshots": [],
              "script_results": [],
              "page_history": []

            }
    # Instead of reassigning DB, update it in place:
    DB.clear()
    DB.update(state)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
