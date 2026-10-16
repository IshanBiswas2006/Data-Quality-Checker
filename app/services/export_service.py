import io
import re
from typing import Tuple, Optional
import pandas as pd
from werkzeug.utils import secure_filename

class ExportService:
    """
    Handles CSV export of cleaned datasets.
    """
    
    @staticmethod
    def sanitize_for_csv(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitizes cell values to prevent CSV formula injection (DDE attacks)
        when opened in spreadsheet software like Excel.
        Prepends a single quote if a text value starts with =, +, -, @, or tab.
        """
        safe_df = df.copy()
        for col in safe_df.columns:
            if pd.api.types.is_string_dtype(safe_df[col]) or safe_df[col].dtype == object:
                safe_df[col] = safe_df[col].apply(
                    lambda v: f"'{v}" if isinstance(v, str) and v and v[0] in ("=", "+", "-", "@", "\t") and not v.replace(".", "", 1).lstrip("-+").isdigit() else v
                )
        return safe_df

    @classmethod
    def export_to_csv_bytes(cls, df: pd.DataFrame, original_filename: str = "dataset.csv", sanitize: bool = True) -> Tuple[Optional[bytes], str, Optional[str]]:
        """
        Exports a DataFrame to CSV bytes.
        
        Returns:
            (csv_bytes, download_filename, error_message)
        """
        try:
            export_df = cls.sanitize_for_csv(df) if sanitize else df
            
            # Format filename
            base_name = original_filename.rsplit(".", 1)[0]
            clean_base = secure_filename(base_name) or "dataset"
            download_name = f"cleaned_{clean_base}.csv"
            
            # Write to UTF-8 with BOM (utf-8-sig) so Excel displays UTF-8 cleanly
            buffer = io.BytesIO()
            export_df.to_csv(buffer, index=False, encoding="utf-8-sig")
            buffer.seek(0)
            
            return buffer.getvalue(), download_name, None
        except Exception as e:
            return None, "cleaned_dataset.csv", f"Export failed: {str(e)}"
