from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import unicodedata

from app.services.sheets_import import import_google_sheet_tickets
from app.services.store import list_ticket_records


try:
    from zoneinfo import ZoneInfo
    PRAGUE_TZ = ZoneInfo("Europe/Prague")
except Exception:
    # Fallback pro Windows / Python 3.14 kde tzdata nefunguje
    PRAGUE_TZ = timezone(timedelta(hours=2))  # CEST = UTC+2 (letni cas)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(PRAGUE_TZ)
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(PRAGUE_TZ)


def _field(row, *names):
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return ""


def _minutes_between(start, end):
    if not start or not end:
        return None
    return max((end - start).total_seconds() / 60, 0)


def _format_dt(value):
    return value.strftime("%d.%m. %H:%M") if value else ""


def _clean_chart_value(value, empty_label="-"):
    text = str(value or "").strip()
    if text in {"", "-", "—", "–", "_"}:
        return empty_label
    if _normalize_text(text) == "as":
        return "AS"
    return text


def _normalize_priority(value):
    text = str(value or "").strip()
    normalized = _normalize_text(text)
    if normalized in {"kriticka", "critical", "hight", "high"}:
        return "High"
    return text


def _is_as_stop(row):
    # Prohledáme všechny relevantní sloupce (i varianty s/bez diakritiky)
    keys = [
        "Popis", "Poznamka", "Poznámka", "Pozn", "Pozn.",
        "Nahlasil", "Nahlásil", "Nahlasil/a", "Nahlásil/a",
        "Technologie", "Typ", "Kategorie",
        "Popis zavady", "Popis závady",
        "description", "reported_by", "technology",
    ]
    combined = " ".join(str(row.get(k, "")) for k in keys)
    normalized = _normalize_text(combined)
    return (
        "system stop alert" in normalized
        or "autostore - system stop alert" in normalized
        or "autostore system stop" in normalized
        or "pozadavek na technika as" in normalized          # z Apps Scriptu: "POŽADAVEK NA TECHNIKA AS"
        or ("noreply-cubeanalytics@autostoresystem.com" in normalized and "has stopped" in normalized)
        or ("cubeanalytics" in normalized and "system stop" in normalized)
    )


def _prepare_row(row):
    # Detekce System Stop
    if _is_as_stop(row):
        row["Technologie"] = "Vypadek AS"
        row["Oddeleni"] = "AS"
        row["Oddělení"] = "AS"
        row["Misto"] = "AutoStore"
        row["Místo"] = "AutoStore"
        row["Priorita"] = "High"

    # Pokud je Technologie ručně nastavena na "Výpadek AS" (s diakritikou), normalizuj
    tech_raw = _normalize_text(str(row.get("Technologie", "")))
    if tech_raw in {"vypadek as", "vypadek-as", "autostore vypadek", "vypadek autostore"}:
        row["Technologie"] = "Vypadek AS"
        row["Oddeleni"] = "AS"
        row["Oddělení"] = "AS"

    reported_at = _parse_datetime(_field(row, "created_at", "reported_at", "Cas nahlaseni", "Čas nahlášení"))
    reacted_at = _parse_datetime(_field(row, "reacted_at", "Cas reakce", "Čas reakce"))
    solved_at = _parse_datetime(_field(row, "solved_at", "Cas vyreseni", "Čas vyřešení"))
    # Oseknout leading apostrof — Google Sheets občas vrací "'V řešení" místo "V řešení"
    status = str(_field(row, "status", "Stav", "Status")).strip().lstrip("'")
    status_norm = _normalize_text(status)

    # Logika: otevřená = prázdný Stav NEBO "V řešení"
    # Vyřešená = jakýkoliv jiný neprázdný Stav (Vyřešeno, Done, Hotovo, ...)
    # Fallback: pokud je vyplněný Čas vyřešení → vždy vyřešeno (i když Stav zapomněli změnit)
    _in_progress_norms = {"v reseni", "v rieseni", "reseni", "rieseni", "in progress", "in_progress"}
    in_progress = status_norm in _in_progress_norms
    solved = (bool(status_norm) and not in_progress) or (solved_at is not None)
    response_min = _minutes_between(reported_at, reacted_at)
    repair_min = _minutes_between(reported_at, solved_at)

    technology = _clean_chart_value(_field(row, "technology", "Technologie"), "Vypadek AS")
    department = _clean_chart_value(_field(row, "department", "Oddělení", "Oddeleni"), "AS")
    location = _clean_chart_value(_field(row, "location", "Místo", "Misto"), "AS")

    if technology == "Vypadek AS":
        department = "AS"
        location = "AS"

    return {
        "reported_at": reported_at,
        "reported_at_text": _format_dt(reported_at),
        "reacted_at_text": _format_dt(reacted_at),
        "solved_at": solved_at,
        "solved_at_text": _format_dt(solved_at),
        "department": department,
        "technology": technology,
        "location": location,
        "priority": _normalize_priority(_field(row, "priority", "Priorita")),
        "description": _field(row, "description", "Popis"),
        "reported_by": _field(row, "reported_by", "Nahlásil", "Nahlasil"),
        "solution": _field(row, "solution", "Popis řešení", "Popis reseni"),
        "status": status,
        "solved": solved,
        "in_progress": in_progress,
        "response_min": response_min,
        "repair_min": repair_min,
        "sla_met": repair_min is not None and repair_min <= 60,
    }


def load_dashboard(days: str = "30", technology: str = "Vse", priority: str = "Vse"):
    raw_rows = list_ticket_records()
    if not raw_rows:
        import_google_sheet_tickets()
        raw_rows = list_ticket_records()

    rows = [_prepare_row(dict(row)) for row in raw_rows]
    rows = [row for row in rows if row["reported_at"]]
    rows.sort(key=lambda row: row["reported_at"], reverse=True)

    base_rows = list(rows)
    now = datetime.now(PRAGUE_TZ)
    if days in {"7", "30"}:
        cutoff = now - timedelta(days=int(days))
        rows = [row for row in rows if row["reported_at"] >= cutoff]

    if technology != "Vse":
        rows = [row for row in rows if row["technology"] == technology]
    if priority != "Vse":
        rows = [row for row in rows if row["priority"] == priority]

    SLA_LIMIT_MIN = 60

    total = len(rows)
    solved = sum(1 for row in rows if row["solved"])
    in_progress = sum(1 for row in rows if row["in_progress"])
    unresolved = total - solved - in_progress
    response_values = [row["response_min"] for row in rows if row["response_min"] is not None]
    repair_values = [row["repair_min"] for row in rows if row["solved"] and row["repair_min"] is not None]
    # SLA se počítá jen ze závad "Vyřešeno" — "V řešení" (čeká na servis/díl) se nezapočítává
    solved_rows = [row for row in rows if row["solved"]]
    sla = round(sum(1 for row in solved_rows if row["sla_met"]) / len(solved_rows) * 100, 1) if solved_rows else 0

    # Předchozí období pro srovnání
    prev_metrics = None
    if days in {"7", "30"}:
        prev_cutoff = cutoff - timedelta(days=int(days))
        prev_rows = [row for row in base_rows if prev_cutoff <= row["reported_at"] < cutoff]
        prev_total = len(prev_rows)
        prev_solved = sum(1 for r in prev_rows if r["solved"])
        prev_unresolved = prev_total - prev_solved - sum(1 for r in prev_rows if r["in_progress"])
        prev_repair = [r["repair_min"] for r in prev_rows if r["solved"] and r["repair_min"] is not None]
        prev_sla = round(sum(1 for r in prev_rows if r["sla_met"]) / prev_total * 100, 1) if prev_total else 0
        prev_metrics = {
            "total": prev_total,
            "solved": prev_solved,
            "unresolved": prev_unresolved,
            "avg_repair": round(sum(prev_repair) / len(prev_repair), 1) if prev_repair else None,
            "sla": prev_sla,
        }

    # SLA přesčasy — závady které překročily 60 min
    def _is_night_shift(row):
        """Noční / večerní směna: nahlášeno v 18:00–05:59 → dlouhá doba opravy je očekávatelná."""
        dt = row.get("reported_at")
        if not dt:
            return False
        h = dt.hour
        return h >= 18 or h < 6

    sla_breaches = [
        {
            "reported_at": row["reported_at_text"],
            "technology": row["technology"],
            "location": row["location"],
            "priority": row["priority"],
            "description": row["description"],
            "repair_min": round(row["repair_min"]),
            "over_by_min": round(row["repair_min"] - SLA_LIMIT_MIN),
            "night_shift": _is_night_shift(row),
        }
        for row in rows
        if row["solved"] and row["repair_min"] is not None and row["repair_min"] > SLA_LIMIT_MIN
    ]
    sla_breaches.sort(key=lambda r: r["over_by_min"], reverse=True)

    # 1. Závady bez popis řešení — vyřešeno ale chybí popis řešení
    no_solution = sorted([
        {
            "reported_at": row["reported_at_text"],
            "technology": row["technology"],
            "location": row["location"],
            "priority": row["priority"],
            "description": row["description"],
            "reported_by": row["reported_by"],
        }
        for row in rows
        if row["solved"] and not str(row.get("solution", "")).strip()
    ], key=lambda x: x["reported_at"], reverse=True)

    # 2. Průměrná doba reakce dle priority
    priority_response: dict = {}
    for row in rows:
        if row["response_min"] is not None:
            p = row["priority"] or "-"
            if p not in priority_response:
                priority_response[p] = []
            priority_response[p].append(row["response_min"])
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    priority_stats = sorted([
        {"priority": p, "avg_response": round(sum(v) / len(v), 1), "count": len(v)}
        for p, v in priority_response.items()
    ], key=lambda x: priority_order.get(x["priority"], 9))

    # 3. Závady dle hodiny dne
    hourly = Counter(row["reported_at"].hour for row in rows if row["reported_at"])
    hourly_chart = [{"hour": h, "count": hourly.get(h, 0)} for h in range(24)]

    # 4. Přehled podle technika (top 10 dle počtu závad)
    tech_data: dict = {}
    for row in rows:
        name = (row["reported_by"] or "").strip()
        if not name:
            continue
        if name not in tech_data:
            tech_data[name] = {"count": 0, "repair_times": []}
        tech_data[name]["count"] += 1
        if row["solved"] and row["repair_min"] is not None:
            tech_data[name]["repair_times"].append(row["repair_min"])
    technicians = sorted([
        {
            "name": name,
            "count": d["count"],
            "avg_repair": round(sum(d["repair_times"]) / len(d["repair_times"]), 1) if d["repair_times"] else None,
        }
        for name, d in tech_data.items()
    ], key=lambda x: x["count"], reverse=True)[:10]

    # 5. Závady vrácené do řešení — stejné místo, nová závada do 24h od vyřešení předchozí
    loc_solved = defaultdict(list)
    for row in rows:
        if row["solved"] and row.get("solved_at") and row["location"] not in {"-", "AS", "AutoStore"}:
            loc_solved[row["location"]].append(row)

    reopened_raw = []
    for row in rows:
        loc = row["location"]
        if not row["reported_at"] or loc in {"-", "AS", "AutoStore"}:
            continue
        for prev in loc_solved.get(loc, []):
            if prev is row:
                continue
            solved_dt = prev.get("solved_at")
            if solved_dt and row["reported_at"] > solved_dt:
                diff_h = (row["reported_at"] - solved_dt).total_seconds() / 3600
                if 0 < diff_h <= 24:
                    reopened_raw.append({
                        "location": loc,
                        "technology": row["technology"],
                        "first_solved": prev["solved_at_text"],
                        "reopened_at": row["reported_at_text"],
                        "hours_between": round(diff_h, 1),
                        "description": row["description"],
                    })
    seen_keys: set = set()
    reopened = []
    for r in sorted(reopened_raw, key=lambda x: x["hours_between"]):
        key = (r["location"], r["reopened_at"])
        if key not in seen_keys:
            seen_keys.add(key)
            reopened.append(r)
    reopened = reopened[:20]

    # Opakující se problémy — místa/technologie s 3+ závadami
    location_counts = Counter(row["location"] for row in rows if row["location"])
    tech_counts = Counter(row["technology"] for row in rows if row["technology"])
    recurring = [
        {"type": "Místo", "name": name, "count": count}
        for name, count in location_counts.most_common(5) if count >= 3
    ] + [
        {"type": "Technologie", "name": name, "count": count}
        for name, count in tech_counts.most_common(5) if count >= 3
    ]
    recurring.sort(key=lambda r: r["count"], reverse=True)

    daily = Counter(row["reported_at"].date().isoformat() for row in rows)
    weekday = Counter(row["reported_at"].strftime("%A") for row in rows)

    def top_counts(key):
        return [{"name": name or "-", "count": count} for name, count in Counter(row[key] for row in rows).most_common(6)]

    all_technologies = sorted({row["technology"] for row in base_rows if row["technology"]})

    table_rows = [
        {
            "reported_at": row["reported_at_text"],
            "technology": row["technology"],
            "location": row["location"],
            "priority": row["priority"],
            "description": row["description"],
            "reported_by": row["reported_by"],
            "status": row["status"],
            "reacted_at": row["reacted_at_text"],
            "solved_at": row["solved_at_text"],
            "solution": row["solution"],
            "hours_open": round((now - row["reported_at"]).total_seconds() / 3600, 1) if not row["solved"] and row["reported_at"] else None,
        }
        for row in rows
    ]

    return {
        "updated_at": now.strftime("%d.%m.%Y %H:%M"),
        "filters": {"technologies": all_technologies},
        "metrics": {
            "total": total,
            "solved": solved,
            "in_progress": in_progress,
            "unresolved": unresolved,
            "solved_percent": round(solved / total * 100, 1) if total else 0,
            "avg_response": round(sum(response_values) / len(response_values), 1) if response_values else None,
            "avg_repair": round(sum(repair_values) / len(repair_values), 1) if repair_values else None,
            "sla": sla,
        },
        "charts": {
            "daily": [{"name": date, "count": count} for date, count in sorted(daily.items())],
            "technology": top_counts("technology"),
            "priority": top_counts("priority"),
            "department": top_counts("department"),
            "location": top_counts("location"),
            "weekday": [{"name": name, "count": weekday.get(name, 0)} for name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]],
        },
        "manager": {
            "prev_metrics": prev_metrics,
            "sla_breaches": sla_breaches[:20],
            "recurring": recurring,
            "no_solution": no_solution[:30],
            "priority_stats": priority_stats,
            "hourly_chart": hourly_chart,
            "technicians": technicians,
            "reopened": reopened,
        },
        "rows": table_rows,
        # Otevřené = hours_open není None (= solved je False = prázdný Stav nebo V řešení)
        "in_progress_rows": [row for row in table_rows if row.get("hours_open") is not None and _normalize_text(str(row["status"])) in {"v reseni", "v rieseni", "reseni", "rieseni", "in progress", "in_progress"}],
        "unresolved_rows": [row for row in table_rows if row.get("hours_open") is not None],
    }
