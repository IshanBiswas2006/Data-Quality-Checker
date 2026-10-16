from flask import request, redirect, url_for, jsonify, current_app, flash
from app.routes import bp_upload
from app.services.file_validator import validate_uploaded_file
from app.services.csv_reader import read_csv_file
from app.services.session_store import SessionStore
from app.services.rate_limiter import SimpleRateLimiter

@bp_upload.route("/upload", methods=["POST"])
def upload_file():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"
    
    # 1. Rate limiting check (e.g. 30 uploads / 10 minutes per IP)
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
        
    allowed, retry_after = SimpleRateLimiter.is_allowed(client_ip, max_requests=40, window_seconds=600)
    if not allowed:
        msg = f"Rate limit exceeded. Please wait {retry_after} seconds before uploading another file."
        if is_ajax:
            resp = jsonify({"success": False, "error": msg})
            resp.status_code = 429
            resp.headers["Retry-After"] = str(retry_after)
            return resp
        flash(msg, "warning")
        return redirect(url_for("main.index")), 429
        
    # 2. File presence check
    if "file" not in request.files:
        msg = "No file part in the request."
        if is_ajax:
            return jsonify({"success": False, "error": msg}), 400
        flash(msg, "error")
        return redirect(url_for("main.index"))
        
    file = request.files["file"]
    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    
    # 3. Server-side file validation (size, extension, empty)
    is_valid, err_msg, sanitized_filename = validate_uploaded_file(file, max_size)
    if not is_valid:
        if is_ajax:
            return jsonify({"success": False, "error": err_msg}), 400
        flash(err_msg, "error")
        return redirect(url_for("main.index"))
        
    # 4. Safe parsing
    df, read_err = read_csv_file(file)
    if read_err or df is None:
        err = read_err or "Failed to read CSV."
        if is_ajax:
            return jsonify({"success": False, "error": err}), 422
        flash(err, "error")
        return redirect(url_for("main.index"))
        
    # 5. Create secure analysis session using sanitized filename (no path components)
    analysis_id = SessionStore.create_session(df, sanitized_filename or "dataset.csv")
    
    redirect_url = url_for("analysis.results", analysis_id=analysis_id)
    if is_ajax:
        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "redirect_url": redirect_url
        }), 200
        
    return redirect(redirect_url)
