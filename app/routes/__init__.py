from flask import Blueprint

bp_main = Blueprint("main", __name__)
bp_upload = Blueprint("upload", __name__)
bp_analysis = Blueprint("analysis", __name__)
bp_cleaning = Blueprint("cleaning", __name__)
bp_download = Blueprint("download", __name__)

from app.routes import main, upload, analysis, cleaning, download
