import io
import csv
from typing import Tuple, Optional, List
import pandas as pd

NA_VALUES: List[str] = [
    "",
    " ",
    "NA",
    "N/A",
    "na",
    "n/a",
    "nan",
    "NaN",
    "NAN",
    "null",
    "NULL",
    "None",
    "none",
    "?",
    "-",
    "--"
]

def read_csv_file(file_source, keep_default_na: bool = True) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely reads CSV content into a pandas DataFrame using multiple encoding strategies
    and delimiter detection.
    
    file_source can be a file path (str/Path), a FileStorage, or a bytes buffer.
    
    Returns:
        (df, error_message)
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    
    # Read raw bytes first to allow multiple decoding attempts
    try:
        if hasattr(file_source, "read"):
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            raw_data = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
        else:
            with open(file_source, "rb") as f:
                raw_data = f.read()
    except Exception as e:
        return None, f"Failed to read file from disk: {str(e)}"
    
    if len(raw_data.strip()) == 0:
        return None, "The CSV file is empty and contains no readable rows or headers."
    
    # Try different encodings
    for encoding in encodings:
        try:
            text_sample = raw_data[:8192].decode(encoding)
            
            # Detect separator
            sep = ","
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(text_sample, delimiters=[",", ";", "\t", "|"])
                sep = dialect.delimiter
            except Exception:
                # Default to comma
                sep = ","
                
            stream = io.BytesIO(raw_data)
            df = pd.read_csv(
                stream,
                encoding=encoding,
                sep=sep,
                na_values=NA_VALUES,
                keep_default_na=keep_default_na,
                dtype=object # read initially as object to preserve raw values and type-inspect accurately
            )
            
            # Strip whitespace from column names if strings
            df.columns = [str(c).strip() for c in df.columns]
            
            if df.empty and len(df.columns) == 0:
                return None, "The CSV file contains no columns or records."
            
            return df, None
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        except pd.errors.EmptyDataError:
            return None, "The CSV file has no data to parse."
        except Exception as e:
            last_err = str(e)
            continue
            
    return None, "Unable to parse CSV. Please verify that the file is a properly formatted, valid CSV file."
