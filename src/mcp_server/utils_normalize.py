# utils_normalize.py
import re, unicodedata

def norm_jp(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[（）\(\)\[\]【】\s]+", "", s)
    s = s.replace("本店", "").replace("別館", "").replace("西口店", "").replace("東口店","")
    return s
