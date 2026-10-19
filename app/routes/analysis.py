from flask import render_template, jsonify, request, redirect, url_for, flash, current_app, g
from app.routes import bp_analysis
from app.services.session_store import SessionStore
from app.services.quality_analyzer import analyze_dataset
from app.services.validation_rules import ValidationRuleEngine
from app.services.report_service import ReportService

@bp_analysis.route("/results/<analysis_id>", methods=["GET"])
def results(analysis_id: str):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"
    if not g.current_user:
        login_url = url_for("auth.login", next=request.path)
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in or sign up to view analysis results.",
                "redirect": login_url
            }), 401
        flash("Please log in or sign up to view analysis results.", "warning")
        return redirect(login_url)

    session = SessionStore.get_session(analysis_id)
    if not session:
        flash("Session expired or invalid analysis ID. Please upload your CSV file again.", "warning")
        return redirect(url_for("main.index"))
        
    preview_limit = current_app.config.get("PREVIEW_ROWS", 10)
    
    original_df = session["original_df"]
    cleaned_df = session["cleaned_df"]
    filename = session["original_filename"]
    operations_history = session["operations_history"]
    
    # Analyze datasets
    analysis_data = analyze_dataset(cleaned_df, preview_rows=preview_limit)
    
    # Calculate comparison
    comparison = ReportService.generate_comparison(original_df, cleaned_df, operations_history)
    
    # Generate visualization charts
    missing_chart_b64 = ReportService.generate_missing_chart(cleaned_df)
    duplicate_chart_b64 = ReportService.generate_duplicate_chart(
        analysis_data["dimensions"]["total_rows"],
        analysis_data["duplicate_summary"]["duplicate_count"]
    )
    
    # Validation rules
    suggested_rules = ValidationRuleEngine.suggest_default_rules(cleaned_df)
    custom_rules = session.get("custom_rules", suggested_rules)
    validation_results = ValidationRuleEngine.validate_rules(cleaned_df, custom_rules)
    
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"
    if is_ajax:
        return jsonify({
            "analysis_id": analysis_id,
            "filename": filename,
            "analysis": analysis_data,
            "comparison": comparison,
            "validation": validation_results,
            "has_changes": len(operations_history) > 0
        })
        
    return render_template(
        "results.html",
        analysis_id=analysis_id,
        filename=filename,
        analysis=analysis_data,
        comparison=comparison,
        missing_chart=missing_chart_b64,
        duplicate_chart=duplicate_chart_b64,
        validation=validation_results,
        suggested_rules=suggested_rules,
        operations_history=operations_history,
        has_changes=len(operations_history) > 0
    )

@bp_analysis.route("/analyze/<analysis_id>", methods=["POST"])
def rerun_analysis(analysis_id: str):
    if not g.current_user:
        return jsonify({
            "success": False,
            "error": "Authentication required. Please log in or sign up.",
            "redirect": url_for("auth.login")
        }), 401

    session = SessionStore.get_session(analysis_id)
    if not session:
        return jsonify({"error": "Session not found or expired."}), 404
        
    preview_limit = current_app.config.get("PREVIEW_ROWS", 10)
    analysis_data = analyze_dataset(session["cleaned_df"], preview_rows=preview_limit)
    comparison = ReportService.generate_comparison(session["original_df"], session["cleaned_df"], session["operations_history"])
    
    return jsonify({
        "success": True,
        "analysis": analysis_data,
        "comparison": comparison
    })

@bp_analysis.route("/validate-rules/<analysis_id>", methods=["POST"])
def validate_rules(analysis_id: str):
    if not g.current_user:
        return jsonify({
            "success": False,
            "error": "Authentication required. Please log in or sign up.",
            "redirect": url_for("auth.login")
        }), 401

    session = SessionStore.get_session(analysis_id)
    if not session:
        return jsonify({"error": "Session not found or expired."}), 404
        
    data = request.get_json(silent=True) or {}
    rules = data.get("rules", [])
    
    session["custom_rules"] = rules
    validation_results = ValidationRuleEngine.validate_rules(session["cleaned_df"], rules)
    
    return jsonify({
        "success": True,
        "validation": validation_results
    })
