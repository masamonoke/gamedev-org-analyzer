from comments import modality

import sys
sys.path.append("../")
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(modality, "modality", 12002, "modality_service", by_symbol=False)
    app.run()

