import os

# Lê a porta via Python — evita o problema de $PORT não ser expandido no shell
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Workers e threads
workers = 2
threads = 4
timeout = 120

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
