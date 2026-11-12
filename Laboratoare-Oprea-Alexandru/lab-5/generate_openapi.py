"""Generate the contract from the FastAPI source, never edit the output manually."""
import json
from pathlib import Path
from api import app
if __name__ == '__main__':
    target=Path(__file__).with_name('openapi.json')
    target.write_text(json.dumps(app.openapi(),indent=2,ensure_ascii=False)+'\n')
    print(f'Generated {target.name}')
