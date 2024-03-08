import sys
sys.path.append("../")
from common.comments import modality
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(modality, "modality", 12002, "modality_service", by_symbol=False)
    app.run()

