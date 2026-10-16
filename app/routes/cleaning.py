from flask import request, jsonify, redirect, url_for, flash, current_app
from app.routes import bp_cleaning
from app.services.session_store import SessionStore
from app.services.cleaning_service import CleaningService
from app.services.quality_analyzer import analyze_dataset
from app.services.report_service import ReportService

@bp_cleaning.route("/clean/<analysis_id>", methods=["POST"])
def clean_dataset(analysis_id: str):
    session = SessionStore.get_session(analysis_id)
    if not session:
        return jsonify({"success": False, "error": "Session expired or invalid analysis ID."}), 404
        
    data = request.get_json(silent=True) or request.form.to_dict()
    
    # Handle operation structure
    op_type = data.get("type") or data.get("operation_type")
    params = data.get("params", {})
    if not isinstance(params, dict):
        params = {}
        
    # If form submission
    if not op_type:
        op_type = data.get("op")
        if op_type == "remove_duplicates":
            params = {}
        elif op_type == "remove_missing":
            params = {"column": data.get("column", "__all__"), "how": data.get("how", "any")}
        elif op_type == "fill_missing":
            params = {
                "column": data.get("column"),
                "strategy": data.get("strategy", "constant"),
                "value": data.get("value", "")
            }
        elif op_type == "convert_type":
            params = {
                "column": data.get("column"),
                "target_type": data.get("target_type")
            }
        elif op_type == "strip_whitespace":
            params = {"column": data.get("column", "__all__")}
        elif op_type == "drop_column":
            params = {"column": data.get("column")}
            
    if not op_type:
        return jsonify({"success": False, "error": "No cleaning operation specified."}), 400
        
    operation = {"type": op_type, "params": params}
    
    # Apply operation on working copy
    new_df, log_entry, err = CleaningService.apply_operation(session["cleaned_df"], operation)
    if err:
        return jsonify({"success": False, "error": err}), 400
        
    # Update session
    SessionStore.update_cleaned(analysis_id, new_df, log_entry)
    
    # Re-calculate preview and comparisons
    preview_limit = current_app.config.get("PREVIEW_ROWS", 10)
    new_analysis = analyze_dataset(new_df, preview_rows=preview_limit)
    new_comparison = ReportService.generate_comparison(session["original_df"], new_df, session["operations_history"])
    
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    if is_ajax:
        return jsonify({
            "success": True,
            "message": log_entry.get("description", "Operation applied successfully."),
            "operation": log_entry,
            "analysis": new_analysis,
            "comparison": new_comparison
        })
        
    flash(log_entry.get("description", "Operation applied."), "success")
    return redirect(url_for("analysis.results", analysis_id=analysis_id))

@bp_cleaning.route("/reset/<analysis_id>", methods=["POST"])
def reset_dataset(analysis_id: str):
    session = SessionStore.get_session(analysis_id)
    if not session:
        return jsonify({"success": False, "error": "Session expired or invalid analysis ID."}), 404
        
    SessionStore.reset_session(analysis_id)
    
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    if is_ajax:
        return jsonify({
            "success": True,
            "message": "Working copy has been reset to the original uploaded data."
        })
        
    flash("Working copy has been reset to original data.", "info")
    return redirect(url_for("analysis.results", analysis_id=analysis_id))
