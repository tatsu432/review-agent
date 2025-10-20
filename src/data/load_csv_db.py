import csv, re, hashlib
from datetime import datetime
from dateutil import parser as dateparser
from unidecode import unidecode
import psycopg

CSV_PATH = "src/data/taberogu/shinjuku_yoyogi_okubo_cleaned.csv"  # your file path
DSN = "postgresql://postgres:postgres@localhost:5432/review_agent"

def rid(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def to_int_safe(s):
    if s is None: return None
    m = re.search(r"\d+", str(s).replace(",", ""))
    return int(m.group()) if m else None

def parse_budget(s):
    # "￥3,000～￥3,999" or "～￥999" or "￥1,000～￥1,999 ￥1,000～￥1,999"
    if not s: return (None,None,None,None)
    parts = str(s).split()
    dinner = parts[0] if len(parts)>0 else None
    lunch  = parts[1] if len(parts)>1 else None

    def parse_range(r):
        if not r: return (None, None)
        nums = [int(x.replace("￥","").replace(",","")) for x in re.findall(r"￥[\d,]+", r)]
        if "～" in r:
            if len(nums)==2: return (nums[0], nums[1])
            if len(nums)==1 and r.startswith("～"): return (0, nums[0])
            if len(nums)==1: return (nums[0], None)
        return (nums[0], nums[0]) if nums else (None, None)

    dmin, dmax = parse_range(dinner)
    lmin, lmax = parse_range(lunch)
    return (dmin, dmax, lmin, lmax)

def parse_bool_from_jp(s, yes_keywords=("有","可","あり"), no_keywords=("無","不可","なし")):
    if s is None: return None
    st = str(s)
    if any(k in st for k in yes_keywords): return True
    if any(k in st for k in no_keywords): return False
    return None

def parse_date_jp(s):
    if not s: return None
    s = str(s)
    # e.g., "2024年12月21日"
    s = s.replace("年","-").replace("月","-").replace("日","")
    try:
        return dateparser.parse(s).date()
    except:
        return None

def norm_categories(s):
    if not s: return []
    return [c.strip() for c in s.split("、") if c.strip()]

def build_retrieval_text(row):
    parts = [
        row["Restaurant_name"],
        f"カテゴリ: {', '.join(row.get('categories', []))}",
        f"レビュー数 {row['review_count']} 食べログ {row.get('star_rating')}",
        f"住所 {row.get('Address','')}",
        f"交通 {row.get('Transportation','')}",
        f"営業時間 {row.get('Operating_hours','')}",
        f"特徴 {row.get('Space_and_facilities','')}",
        f"料理 {row.get('Dishes','')}",
        f"シーン {row.get('Occasion','')}",
        f"子供可 {row.get('With_children')}",
        f"喫煙 {row.get('No_smoking_or_Smoking')}",
    ]
    return " / ".join([p for p in parts if p])

def clean_ward(address):
    # crude: extract '東京都新宿区' -> ward = '新宿区'
    if not address: return None
    m = re.search(r"東京都?([^市区町村]+区)", address)
    return m.group(1) if m else None

def area_hint_from_transport(s):
    if not s: return None
    m = re.search(r"(新宿|新大久保|大久保|渋谷|恵比寿|池袋|品川|上野|神田|中野|高田馬場)", s)
    return m.group(1) if m else None


def load_csv_to_db(csv_path: str = CSV_PATH, dsn: str = DSN) -> None:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            page_url = r["Page_URL"].strip()
            row = {}
            row["restaurant_id"] = rid(page_url)
            row["Restaurant_name"] = r["Restaurant_name"].strip()
            row["page_url"] = page_url
            # numbers
            try:
                row["star_rating"] = float(r["Star_rating"]) if r["Star_rating"] else None
            except:
                row["star_rating"] = None
            row["review_count"] = to_int_safe(r["Number_Of_Reviewers"])
            # arrays/booleans
            row["categories"] = norm_categories(r["Categories"])
            row["tel_reservation"] = r.get("Tel_for_reservation") or None
            row["tel"] = r.get("Tel") or None
            row["address"] = r.get("Address") or None
            row["ward"] = clean_ward(row["address"])
            row["area_hint"] = area_hint_from_transport(r.get("Transportation",""))
            row["transportation"] = r.get("Transportation") or None
            dmin,dmax,lmin,lmax = parse_budget(r.get("Budget"))
            row["budget_dinner_min"]=dmin; row["budget_dinner_max"]=dmax
            row["budget_lunch_min"]=lmin;  row["budget_lunch_max"]=lmax
            row["payment_methods"] = r.get("Method_of_payment") or None
            row["table_money"] = r.get("Table_money") or None
            row["seats"] = to_int_safe(r.get("Number_of_seats"))
            row["private_room"] = parse_bool_from_jp(r.get("Private_dining_room"))
            row["private_use"] = parse_bool_from_jp(r.get("Private_use"))
            row["smoking"] = r.get("No_smoking_or_Smoking") or None
            row["parking"] = parse_bool_from_jp(r.get("Parking_lot"))
            row["space_facilities"] = r.get("Space_and_facilities") or None
            row["course"] = r.get("Course") or None
            row["drink"] = r.get("Drink") or None
            row["dishes"] = r.get("Dishes") or None
            row["occasion"] = r.get("Occasion") or None
            row["location_tags"] = r.get("Location") or None
            row["service"] = r.get("Service") or None
            row["with_children"] = parse_bool_from_jp(r.get("With_children"))
            row["homepage"] = r.get("The_homepage") or None
            row["opening_day"] = parse_date_jp(r.get("The_opening_day"))
            row["remarks"] = r.get("Remarks") or None
            row["first_reviewer"] = r.get("First_Reviewers") or None
            row["Operating_hours"] = r.get("Operating_hours") or None
            row["Space_and_facilities"] = r.get("Space_and_facilities") or None
            row["Dishes"] = r.get("Dishes") or None
            row["Occasion"] = r.get("Occasion") or None
            row["With_children"] = r.get("With_children") or None
            row["No_smoking_or_Smoking"] = r.get("No_smoking_or_Smoking") or None

            row["retrieval_text_ja"] = build_retrieval_text(row)
            rows.append(row)

    with psycopg.connect(DSN) as con, con.cursor() as cur:
        for r in rows:
            cur.execute("""
                INSERT INTO restaurants (
                restaurant_id, name, page_url, star_rating, review_count, categories,
                tel_reservation, tel, address, ward, area_hint, transportation,
                budget_dinner_min, budget_dinner_max, budget_lunch_min, budget_lunch_max,
                payment_methods, table_money, seats, private_room, private_use, smoking,
                parking, space_facilities, course, drink, dishes, occasion, location_tags,
                service, with_children, homepage, opening_day, remarks, first_reviewer,
                retrieval_text_ja
                ) VALUES (
                %(restaurant_id)s, %(Restaurant_name)s, %(page_url)s, %(star_rating)s, %(review_count)s, %(categories)s,
                %(tel_reservation)s, %(tel)s, %(address)s, %(ward)s, %(area_hint)s, %(transportation)s,
                %(budget_dinner_min)s, %(budget_dinner_max)s, %(budget_lunch_min)s, %(budget_lunch_max)s,
                %(payment_methods)s, %(table_money)s, %(seats)s, %(private_room)s, %(private_use)s, %(smoking)s,
                %(parking)s, %(space_facilities)s, %(course)s, %(drink)s, %(dishes)s, %(occasion)s, %(location_tags)s,
                %(service)s, %(with_children)s, %(homepage)s, %(opening_day)s, %(remarks)s, %(first_reviewer)s,
                %(retrieval_text_ja)s
                )
                ON CONFLICT (restaurant_id) DO UPDATE SET
                name=EXCLUDED.name,
                star_rating=EXCLUDED.star_rating,
                review_count=EXCLUDED.review_count,
                categories=EXCLUDED.categories,
                address=EXCLUDED.address,
                ward=EXCLUDED.ward,
                area_hint=EXCLUDED.area_hint,
                retrieval_text_ja=EXCLUDED.retrieval_text_ja,
                updated_at=now();
            """, r)
        con.commit()
    print(f"Loaded {len(rows)} rows.")
