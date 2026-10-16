import os
from flask import Flask, render_template, request, jsonify
from config import Config, config_by_name

def create_app(config_name=None, config_class=None) -> Flask:
    app = Flask(__name__)
    
    if config_class:
        app.config.from_object(config_class)
    elif config_name and config_name in config_by_name:
        app.config.from_object(config_by_name[config_name])
    else:
        env = os.environ.get("FLASK_ENV", "development")
        app.config.from_object(config_by_name.get(env, Config))
    
    # Ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "temp_uploads"), exist_ok=True)
    
    # Register blueprints
    from app.routes import bp_main, bp_upload, bp_analysis, bp_cleaning, bp_download
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_upload)
    app.register_blueprint(bp_analysis)
    app.register_blueprint(bp_cleaning)
    app.register_blueprint(bp_download)
    
    # Apply security headers to every response
    @app.after_request
    def set_security_headers(response):
        sec_headers = app.config.get("SECURITY_HEADERS", {})
        for header, value in sec_headers.items():
            response.headers[header] = value
        return response
    
    # Error handlers with safe messages and correct status codes
    @app.errorhandler(400)
    def bad_request(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": False, "error": "Bad request"}), 400
        return render_template("errors/400.html", error="Bad request"), 400
        
    @app.errorhandler(404)
    def not_found(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": False, "error": "Resource not found"}), 404
        return render_template("errors/404.html"), 404
        
    @app.errorhandler(413)
    def file_too_large(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": False, "error": "File exceeds upload limit"}), 413
        return render_template("errors/413.html"), 413
        
    @app.errorhandler(429)
    def rate_limited(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": False, "error": "Rate limit exceeded"}), 429
        return render_template("errors/400.html", error="Too many requests. Please try again shortly."), 429

    @app.errorhandler(500)
    def internal_error(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": False, "error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    return app
