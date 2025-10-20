import pandas as pd

def clean_text(text):
    """Clean text by removing newlines and extra whitespace"""
    if pd.isna(text):
        return text
    # Convert to string, remove newlines, and clean whitespace
    cleaned = str(text).replace("\n", " ").replace("\r", " ")
    # Remove extra whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()

def clean_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].apply(clean_text)
    return df

def save_csv(df: pd.DataFrame, output_csv_path: str) -> None:
    df.to_csv(output_csv_path, index=False, encoding="utf-8")