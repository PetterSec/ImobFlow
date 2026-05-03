from app import create_app
from datetime import datetime
import os

# Carrega .env automaticamente em desenvolvimento
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Em produção (Railway) não precisa de dotenv

app = create_app()

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


@app.context_processor
def inject_monetization_settings():
    """Templates: show_ads_free, adsense_client, adsense_slot (planos Free + AdSense)."""
    return {
        "show_ads_free": app.config.get("SHOW_ADS_ON_FREE_PLAN", False),
        "adsense_client": app.config.get("GOOGLE_ADSENSE_CLIENT", ""),
        "adsense_slot": app.config.get("GOOGLE_ADSENSE_SLOT", ""),
    }

# Necessário apenas para rodar localmente com `python run.py`
# No Railway o Gunicorn chama `run:app` diretamente
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)