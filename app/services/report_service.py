import io
import base64
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

class ReportService:
    """
    Generates structured reports, comparisons, and visualizations.
    """
    
    @staticmethod
    def generate_comparison(original_df: pd.DataFrame, cleaned_df: pd.DataFrame, operations_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates before-and-after comparison metrics between the original and cleaned dataset.
        """
        orig_rows = len(original_df)
        clean_rows = len(cleaned_df)
        rows_removed = orig_rows - clean_rows
        
        orig_cols = len(original_df.columns)
        clean_cols = len(cleaned_df.columns)
        
        # Missing values
        orig_missing = int((original_df.isna() | original_df.apply(lambda s: s.astype(str).str.strip().isin(["", "nan", "None", "null"]))).sum().sum())
        clean_missing = int((cleaned_df.isna() | cleaned_df.apply(lambda s: s.astype(str).str.strip().isin(["", "nan", "None", "null"]))).sum().sum())
        missing_resolved = orig_missing - clean_missing
        
        # Duplicates
        orig_dups = int(original_df.duplicated(keep="first").sum())
        clean_dups = int(cleaned_df.duplicated(keep="first").sum())
        dups_removed = orig_dups - clean_dups
        
        return {
            "original": {
                "rows": orig_rows,
                "columns": orig_cols,
                "missing_values": orig_missing,
                "duplicates": orig_dups
            },
            "cleaned": {
                "rows": clean_rows,
                "columns": clean_cols,
                "missing_values": clean_missing,
                "duplicates": clean_dups
            },
            "delta": {
                "rows_removed": rows_removed,
                "columns_changed": clean_cols - orig_cols,
                "missing_values_resolved": missing_resolved,
                "duplicates_removed": dups_removed
            },
            "operations_applied": operations_history or []
        }

    @staticmethod
    def generate_missing_chart(df: pd.DataFrame) -> Optional[str]:
        """
        Generates a clean bar chart of missing values per column as a base64 PNG.
        Uses clean minimalist styling per Design.md tokens.
        """
        missing_counts = {}
        for col in df.columns:
            cnt = int((df[col].isna() | df[col].astype(str).str.strip().isin(["", "nan", "None", "null"])).sum())
            if cnt > 0:
                missing_counts[col] = cnt
                
        if not missing_counts:
            return None
            
        fig, ax = plt.subplots(figsize=(7, 3.2), dpi=120)
        fig.patch.set_facecolor("#1B1F24")
        ax.set_facecolor("#1B1F24")
        
        cols = list(missing_counts.keys())
        counts = list(missing_counts.values())
        
        bars = ax.barh(cols, counts, color="#5B8BF7", edgecolor="#353A42", height=0.55)
        
        ax.tick_params(colors="#B7BBC2", labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#353A42")
        ax.spines["left"].set_color("#353A42")
        
        ax.set_xlabel("Missing Values Count", color="#F2F3F5", fontsize=10, labelpad=8)
        ax.set_title("Missing Values by Column", color="#F2F3F5", fontsize=11, fontweight="bold", pad=12)
        
        # Add value labels on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                    f"{int(width)}",
                    va="center", ha="left", color="#F2F3F5", fontsize=9)
                    
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
        
    @staticmethod
    def generate_duplicate_chart(total_rows: int, duplicate_rows: int) -> Optional[str]:
        """
        Generates a clean donut/pie chart for duplicate vs unique rows.
        """
        if total_rows == 0:
            return None
            
        unique_rows = total_rows - duplicate_rows
        
        fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=120)
        fig.patch.set_facecolor("#1B1F24")
        ax.set_facecolor("#1B1F24")
        
        labels = ["Unique", "Duplicate"] if duplicate_rows > 0 else ["Unique (100%)"]
        sizes = [unique_rows, duplicate_rows] if duplicate_rows > 0 else [unique_rows]
        colors = ["#2E7D32", "#E53935"] if duplicate_rows > 0 else ["#2E7D32"]
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=140,
            textprops=dict(color="#F2F3F5", fontsize=9),
            wedgeprops=dict(width=0.45, edgecolor="#1B1F24")
        )
        
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontweight("bold")
            
        ax.set_title("Row Uniqueness", color="#F2F3F5", fontsize=11, fontweight="bold", pad=10)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
