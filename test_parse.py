import json, re

def find_script():
    with open('microsoft-techcommunity/articles/4540160.html', 'r', encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    return None

data = find_script()

def recurse_json(val, path=""):
    targets = ["body", "content", "message", "subject", "author", "article"]
    if isinstance(val, dict):
        for k, v in val.items():
            current_path = f"{path}.{k}" if path else k
            # Check if current key matches
            if any(t in k.lower() for t in targets):
                v_type = type(v).__name__
                # Get a preview or length
                if isinstance(v, (str, bytes)):
                    preview = v[:100] + "..." if len(v) > 100 else v
                    print(f"Path: {current_path} | Type: {v_type} | Length/Preview: {len(v)} - {repr(preview)}")
                elif isinstance(v, (dict, list)):
                    print(f"Path: {current_path} | Type: {v_type} | Length/Preview: Size {len(v)}")
                else:
                    print(f"Path: {current_path} | Type: {v_type} | Length/Preview: {v}")

            # Recurse
            recurse_json(v, current_path)
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            current_path = f"{path}[{idx}]"
            recurse_json(item, current_path)

if data:
    recurse_json(data)
