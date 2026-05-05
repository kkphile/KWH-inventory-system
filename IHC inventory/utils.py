import datetime
from tkinter import messagebox

def is_valid_date(date_text, parent_window):
    """
    Checks if the provided date string is valid.
    If valid, returns the strictly formatted date (YYYY-MM-DD) with padded zeros.
    If invalid, triggers a standardized error popup and returns False.
    """
    cleaned_date = date_text.strip()
    
    if not cleaned_date:
        return "" 

    try:
        # 1. Parse the string into a datetime object
        # This function natively understands "2026-3-3" as a valid format
        parsed_date = datetime.datetime.strptime(cleaned_date, "%Y-%m-%d")
        
        # 2. Format the datetime object back into a strict string (adds leading zeros)
        formatted_date = parsed_date.strftime("%Y-%m-%d")
        
        # 3. Return the corrected string
        return formatted_date
        
    except ValueError:
        messagebox.showerror(
            "Format Error", 
            "Invalid date format!\n\nPlease use YYYY-MM-DD (e.g., 2026-12-31).", 
            parent=parent_window
        )
        return False