import pandas as pd
import re

# Normalize a raw matched string -> return 10-digit string or "" if invalid
def normalize_number(raw):
    if not raw:
        return ""
    # keep digits only
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    # if starts with country code '91' and length > 10, take last 10
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[-10:]
    # if leading zero and 11 digits, drop the zero
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    # final check: must be exactly 10 digits and start with 6-9 (Indian mobile)
    if len(digits) == 10 and re.match(r"^[6-9]\d{9}$", digits):
        return digits
    return ""

# Extract all possible phone-like substrings from text and normalize them
def extract_phones_from_text(text):
    if not isinstance(text, str):
        text = str(text)
    # patterns to catch +91..., 0xxxxxxxxxx, or plain 10 digit (allow separators)
    # we'll search for sequences that could represent numbers (digits plus optional +)
    candidates = re.findall(r'(?:\+91[\-\s]*\d{10})|(?:0\d{10})|(?:\d{10})', text)
    normalized = []
    for cand in candidates:
        n = normalize_number(cand)
        if n:
            normalized.append(n)
    # also try to find numbers that may be written with separators like 987-654-3210 or 987 654 3210
    if not normalized:
        alt = re.findall(r'(?:\+91[\-\s]*(?:\d[\-\s]*){10})|(?:0(?:\d[\-\s]*){10})|(?:(?:\d[\-\s]*){10})', text)
        for cand in alt:
            n = normalize_number(cand)
            if n:
                normalized.append(n)
    # unique preserve order
    seen = set()
    uniq = []
    for x in normalized:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def process_file(input_path, output_path="clean_data.csv"):
    df = pd.read_csv(input_path, dtype=str).fillna("")  # keep everything as string
    out_rows = []

    # determine address/details columns if present
    possible_text_cols = ["Details", "details", "Address", "address", "Profile Link", "Profile_Link", "profile_link"]
    for idx, row in df.iterrows():
        name = row.get("Name", "") or row.get("name", "")
        # pick an address column if exists
        address = ""
        for c in ["Address", "address"]:
            if c in df.columns and row.get(c, "").strip():
                address = row.get(c, "").strip()
                break
        # combine candidate text sources to search for phone numbers
        combined_text_parts = []
        for c in df.columns:
            # include columns that likely contain the scraped visible text
            if c.lower() in ("details", "detail", "about", "description", "profile link", "profile_link", "address", "phone"):
                combined_text_parts.append(row.get(c, ""))
        # also include all columns as fallback
        if not combined_text_parts:
            combined_text_parts = [str(row[col]) for col in df.columns]

        combined_text = " | ".join(combined_text_parts)

        phones = extract_phones_from_text(combined_text)

        phone_field = ",".join(phones) if phones else ""

        out_rows.append({
            "Name": name,
            "Address": address,
            "Phone": phone_field
        })

    out_df = pd.DataFrame(out_rows, columns=["Name", "Address", "Phone"])
    out_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"✅ Done — cleaned file saved as: {output_path}")

if __name__ == "__main__":
    inp = input("Enter input CSV path (scraped file): ").strip()
    out = input("Enter output CSV path (default: clean_data.csv): ").strip() or "clean_data.csv"
    process_file(inp, out)
