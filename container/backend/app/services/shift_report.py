from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import unicodedata

from app.services.dashboard import PRAGUE_TZ, _parse_datetime
from app.services.store import list_ticket_records


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value or "").lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _minutes_between(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None
    return max(round((end - start).total_seconds() / 60), 0)


def _format_minutes(value: float | None) -> str:
    if value is None:
        return "neni k dispozici"
    total = round(value)
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    if hours:
        return f"{hours} h"
    return f"{minutes} min"


def _avg(values: list[int | None]) -> float | None:
    valid = [v for v in values if v is not None]
    return round(sum(valid) / len(valid), 1) if valid else None


def _is_resolved(row: dict) -> bool:
    status = _normalize(row.get("status"))
    return bool(row.get("solved_at")) or any(word in status for word in ["vyreseno", "resolved", "closed", "hotovo"])


def _row_to_ticket(row: dict) -> dict:
    reported_at = _parse_datetime(row.get("created_at") or row.get("reported_at"))
    reacted_at = _parse_datetime(row.get("reacted_at"))
    solved_at = _parse_datetime(row.get("solved_at"))
    return {
        "reported_at": reported_at,
        "reacted_at": reacted_at,
        "solved_at": solved_at,
        "response_min": _minutes_between(reported_at, reacted_at),
        "repair_min": _minutes_between(reported_at, solved_at),
        "department": row.get("department") or "",
        "technology": row.get("technology") or "Ostatni",
        "location": row.get("location") or "",
        "priority": row.get("priority") or "",
        "description": row.get("description") or "",
        "status": row.get("status") or "",
        "reported_by": row.get("reported_by") or "",
        "resolved": _is_resolved(row),
    }


def _target_dates(run_at: datetime) -> tuple[datetime, datetime]:
    run_day = datetime(run_at.year, run_at.month, run_at.day, tzinfo=PRAGUE_TZ)
    target = run_day - timedelta(days=1)
    prev = target - timedelta(days=1)
    return prev, target


def _in_shift(ticket: dict, shift: str, prev: datetime, target: datetime) -> bool:
    reported_at = ticket.get("reported_at")
    if not reported_at:
        return False
    minute = reported_at.hour * 60 + reported_at.minute
    day = reported_at.date()
    if shift == "day":
        return day == target.date() and 360 <= minute < 1080
    return (day == prev.date() and minute >= 1080) or (day == target.date() and minute < 360)


def _summarize(label: str, tickets: list[dict]) -> dict:
    open_tickets = [ticket for ticket in tickets if not ticket["resolved"]]
    resolved = len(tickets) - len(open_tickets)
    recurring_counts = Counter(ticket["technology"] for ticket in tickets if ticket["technology"])
    recurring = [
        {"name": name, "count": count}
        for name, count in recurring_counts.most_common(5)
        if count >= 2
    ]
    avg_response = _avg([ticket["response_min"] for ticket in tickets])
    avg_repair = _avg([ticket["repair_min"] for ticket in tickets])
    handover = [
        {
            "technology": ticket["technology"],
            "location": ticket["location"],
            "priority": ticket["priority"],
            "description": ticket["description"],
            "reported_at": ticket["reported_at"].isoformat() if ticket["reported_at"] else "",
        }
        for ticket in open_tickets[:10]
    ]

    if not tickets:
        sentence = f"{label} nema v evidenci zadne zavady."
    else:
        recurring_sentence = ""
        if recurring:
            top = recurring[0]
            recurring_sentence = f" Nej castejsi technologie byla {top['name']}, vyskyt {top['count']}x."
        handover_sentence = (
            f" K predani zustava {len(open_tickets)} otevrenych zavad."
            if open_tickets
            else " K predani nezustava zadna otevrena zavada."
        )
        sentence = (
            f"{label} resila celkem {len(tickets)} zavad, z toho {resolved} bylo vyreseno. "
            f"Prumerna reakce byla {_format_minutes(avg_response)} a prumerny cas opravy {_format_minutes(avg_repair)}."
            f"{recurring_sentence}{handover_sentence}"
        )

    return {
        "total": len(tickets),
        "resolved": resolved,
        "open": len(open_tickets),
        "avg_response_min": avg_response,
        "avg_response_text": _format_minutes(avg_response),
        "avg_repair_min": avg_repair,
        "avg_repair_text": _format_minutes(avg_repair),
        "recurring": recurring,
        "handover": handover,
        "sentence": sentence,
    }


def _render_text(night: dict, day: dict, prev: datetime, target: datetime) -> str:
    def block(title: str, date_range: str, summary: dict) -> str:
        recurring = "\n".join(f"- {item['name']}: {item['count']}x" for item in summary["recurring"]) or "- Bez opakujicich se zavad."
        handover = "\n".join(
            f"- {item['technology']} | {item['location']}: {item['description'] or 'bez popisu'}"
            for item in summary["handover"]
        ) or "Vse vyreseno."
        return (
            f"{title}\n{date_range}\n"
            f"----------------------------------------\n"
            f"Celkem zavad: {summary['total']}\n"
            f"Vyreseno: {summary['resolved']}\n"
            f"Nevyreseno: {summary['open']}\n"
            f"Prum. reakce: {summary['avg_response_text']}\n"
            f"Prum. oprava: {summary['avg_repair_text']}\n\n"
            f"OPAKUJICI SE ZAVADY\n{recurring}\n\n"
            f"K PREDANI\n{handover}\n\n"
            f"REPORT\n{summary['sentence']}"
        )

    return "\n\n".join(
        [
            block(
                "NOCNI SMENA",
                f"{prev.strftime('%d.%m.%Y')} 18:00 - {target.strftime('%d.%m.%Y')} 06:00",
                night,
            ),
            block(
                "DENNI SMENA",
                f"{target.strftime('%d.%m.%Y')} 06:00 - 18:00",
                day,
            ),
        ]
    )


def build_shift_summary(run_at: datetime | None = None) -> dict:
    run_at = (run_at or datetime.now(PRAGUE_TZ)).astimezone(PRAGUE_TZ)
    prev, target = _target_dates(run_at)
    tickets = [_row_to_ticket(row) for row in list_ticket_records()]
    tickets = [ticket for ticket in tickets if ticket["reported_at"]]

    night_tickets = [ticket for ticket in tickets if _in_shift(ticket, "night", prev, target)]
    day_tickets = [ticket for ticket in tickets if _in_shift(ticket, "day", prev, target)]
    night = _summarize("Nocni smena", night_tickets)
    day = _summarize("Denni smena", day_tickets)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_date": target.date().isoformat(),
        "night_range": {
            "from": prev.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
            "to": target.replace(hour=6, minute=0, second=0, microsecond=0).isoformat(),
        },
        "day_range": {
            "from": target.replace(hour=6, minute=0, second=0, microsecond=0).isoformat(),
            "to": target.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
        },
        "night": night,
        "day": day,
        "text": _render_text(night, day, prev, target),
    }
