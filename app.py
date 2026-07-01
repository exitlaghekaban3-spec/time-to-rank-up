from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'anime-stars-rank-calculator-secret-key'

# =====================================================================
# 1. FULL LIST OF SUFFIXES FOR SELECTION
# =====================================================================
SUFFIXES = {
    'K': 1_000,
    'M': 1_000_000,
    'B': 1_000_000_000,
    'T': 1_000_000_000_000,
    'Qa': 1_000_000_000_000_000,
    'Qi': 1_000_000_000_000_000_000,
    'Sx': 1_000_000_000_000_000_000_000,
    'Sp': 1_000_000_000_000_000_000_000_000,
    'Oc': 1_000_000_000_000_000_000_000_000_000,
    'No': 1_000_000_000_000_000_000_000_000_000_000,
    'De': 1_000_000_000_000_000_000_000_000_000_000_000,
    'βA': 1_000_000_000_000_000_000_000_000_000_000_000_000,
    'βB': 1_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βC': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βD': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βE': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βF': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βG': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βH': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βI': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βJ': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βK': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βL': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'βM': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
}

# Raw definitions to cleanly build values and lookups
RAW_RANKS = {
    1: "15K", 2: "200K", 3: "1.5M", 4: "10.5M", 5: "70M", 6: "455M", 7: "2.5B", 8: "12.5B",
    9: "50B", 10: "225B", 11: "1.1T", 12: "7.5T", 13: "52.5T", 14: "395T", 15: "3.1Qa",
    16: "27.5Qa", 17: "245Qa", 18: "2.4Qa", 19: "23.2Qi", 20: "245Qi", 21: "2.7Sx",
    22: "31.5Sx", 23: "350Sx", 24: "7.5Sp", 25: "125Sp", 26: "2.5Oc", 27: "25Oc",
    28: "750Oc", 29: "30No", 30: "1.4De", 31: "82.5De", 32: "7.5βA", 33: "260βA",
    34: "16βB", 35: "1.1βC", 36: "85βC", 37: "4.5βD", 38: "36βD", 39: "430βD",
    40: "6.9βE", 41: "165βE", 42: "5.8βF"
}

def parse_rank_value(val_str):
    val_str = str(val_str).strip().replace(',', '.')
    
    # Сортируем суффиксы от самых длинных к самым коротким, 
    # чтобы 'βB' проверялся раньше, чем одиночная 'B'
    sorted_suffixes = sorted(SUFFIXES.items(), key=lambda x: len(x[0]), reverse=True)
    
    for suffix, multiplier in sorted_suffixes:
        if val_str.endswith(suffix):
            num_part = val_str[:-len(suffix)].strip()
            try:
                return float(num_part) * multiplier
            except ValueError:
                pass
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def format_game_number(num):
    if num == 0:
        return "0"
    abs_num = abs(num)
    for suffix, multiplier in sorted(SUFFIXES.items(), key=lambda x: x[1], reverse=True):
        if abs_num >= multiplier:
            formatted = f"{num / multiplier:.2f}".rstrip('0').rstrip('.')
            return f"{formatted}{suffix}"
    return f"{num:.2f}".rstrip('0').rstrip('.')

RANKS_NUMERIC = {r: parse_rank_value(v) for r, v in RAW_RANKS.items()}

# Generated tuple for template select menu: (rank_number, "Rank X (Value)")
RANKS_SELECT_OPTIONS = [(r, f"Rank {r} ({v})") for r, v in RAW_RANKS.items()]

def format_time(seconds):
    if seconds <= 0:
        return "0s"
    minutes = seconds // 60
    remaining_seconds = int(seconds % 60)
    hours = minutes // 60
    remaining_minutes = int(minutes % 60)
    days = hours // 24
    remaining_hours = int(hours % 24)
    
    parts = []
    if days > 0: parts.append(f"{int(days)}d")
    if hours > 0: parts.append(f"{remaining_hours}h")
    if minutes > 0: parts.append(f"{remaining_minutes}m")
    if remaining_seconds > 0 or not parts: parts.append(f"{remaining_seconds}s")
    return " ".join(parts)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        multiplier_raw = request.form.get("multiplier", "0").replace(',', '.')
        selected_suffix = request.form.get("suffix", "")
        target_rank = int(request.form.get("rank", "1"))
        has_fast_click = request.form.get("fast_click") == "yes"
        
        try:
            base_multiplier = float(multiplier_raw)
        except ValueError:
            base_multiplier = 0.0
            
        suffix_value = SUFFIXES.get(selected_suffix, 1)
        total_multiplier = base_multiplier * suffix_value
        clicks_per_second = 3.66 if has_fast_click else 2.66
        power_per_second = total_multiplier * clicks_per_second
        required_power = RANKS_NUMERIC.get(target_rank, 0.0)
        
        if power_per_second > 0:
            time_formatted = format_time(required_power / power_per_second)
        else:
            time_formatted = "Infinite (Enter a valid multiplier)"
            
        # Store results AND form inputs to avoid resets
        session["rank_calc_data"] = {
            "result": {
                "rank": target_rank,
                "required_power": RAW_RANKS.get(target_rank),
                "clicks_speed": clicks_per_second,
                "time_needed": time_formatted
            },
            "inputs": {
                "multiplier": multiplier_raw,
                "suffix": selected_suffix,
                "rank": target_rank,
                "fast_click": "yes" if has_fast_click else "no"
            }
        }
        return redirect(url_for("index"))
        
    data = session.pop("rank_calc_data", None)
    result = data.get("result") if data else None
    inputs = data.get("inputs") if data else {"multiplier": "", "suffix": "", "rank": 1, "fast_click": "no"}
    
    return render_template("index.html", suffixes=SUFFIXES.keys(), ranks_options=RANKS_SELECT_OPTIONS, result=result, inputs=inputs)

if __name__ == "__main__":
    app.run(debug=True)