import io
from flask import send_file, flash, redirect, url_for, jsonify, request, g
from app.routes import bp_download
from app.services.session_store import SessionStore
from app.services.export_service import ExportService

@bp_download.route("/download/<analysis_id>", methods=["GET"])
def download_cleaned(analysis_id: str):
    if not g.current_user:
        flash("Please log in or sign up to download datasets.", "warning")
        return redirect(url_for("auth.login", next=request.path))

    session = SessionStore.get_session(analysis_id)
    if not session:
        flash("Analysis session expired. Please re-upload your file.", "warning")
        return redirect(url_for("main.index"))
        
    csv_bytes, filename, err = ExportService.export_to_csv_bytes(
        session["cleaned_df"],
        session["original_filename"]
    )
    
    if err or not csv_bytes:
        flash(err or "Failed to generate CSV export.", "error")
        return redirect(url_for("analysis.results", analysis_id=analysis_id))
        
    return send_file(
        io.BytesIO(csv_bytes),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )
