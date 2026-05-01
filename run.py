from app import create_app
from datetime import datetime
import os

app = create_app()

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
