"""The four tools the voice agents call. Retell and Vapi both use these."""

from datetime import datetime, timedelta, timezone

import db

VALID_TYPES = ["fire", "electrical", "osha", "environmental", "comprehensive"]
SLOTS = ["08:00-10:00", "10:00-12:00", "13:00-15:00", "15:00-17:00"]


async def lookup_customer(phone: str | None = None, name: str | None = None, company: str | None = None) -> dict:
    customer = await db.pool.fetchrow(
        "SELECT * FROM customers WHERE phone = $1 OR lower(name) = lower($2) OR lower(company) = lower($3) LIMIT 1",
        phone,
        name,
        company,
    )
    if not customer:
        return {"error": "No customer found. Ask for a different detail (phone, name, or company)."}

    upcoming = await db.pool.fetch(
        "SELECT id, type, date, time_slot FROM inspections WHERE customer_id = $1 AND status = 'confirmed' ORDER BY date",
        customer["id"],
    )

    # Store summary: for every store, its last inspection and how many inspections it failed in the past year.
    one_year_ago = (datetime.now() - timedelta(days=365)).date().isoformat()
    stores = await db.pool.fetch("SELECT * FROM stores WHERE customer_id = $1 ORDER BY id", customer["id"])
    stores_with_failures = []
    for store in stores:
        last_inspection = await db.pool.fetchval(
            "SELECT date FROM inspection_history WHERE store_id = $1 ORDER BY date DESC LIMIT 1",
            store["id"],
        )
        failed = await db.pool.fetchval(
            "SELECT count(*) FROM inspection_history WHERE store_id = $1 AND result = 'fail' AND date >= $2",
            store["id"],
            one_year_ago,
        )
        if failed > 0:
            stores_with_failures.append(
                {"store": store["name"], "failed_inspections": failed, "last_inspection": last_inspection}
            )

    return {
        "customer": dict(customer),
        "upcoming_inspections": [dict(row) for row in upcoming],
        "total_stores": len(stores),
        "stores_with_failures_last_year": len(stores_with_failures),
        "stores_needing_attention": stores_with_failures[:3],
    }


def booking_problem(date: str, inspection_type: str) -> str | None:
    """Why this date and type can't be booked, or None if they can."""
    if inspection_type not in VALID_TYPES:
        return f"Unknown inspection type. Use one of: {', '.join(VALID_TYPES)}."
    if date < datetime.now(timezone.utc).date().isoformat():
        return f"{date} is in the past."
    if datetime.fromisoformat(date).weekday() >= 5:
        return f"{date} is a weekend. Inspections are weekdays only."
    return None


async def check_availability(date: str, inspection_type: str) -> dict:
    problem = booking_problem(date, inspection_type)
    if problem:
        return {"error": problem}

    rows = await db.pool.fetch("SELECT time_slot FROM inspections WHERE date = $1 AND status = 'confirmed'", date)
    booked = [row["time_slot"] for row in rows]
    return {"available_slots": [slot for slot in SLOTS if slot not in booked]}


async def book_inspection(customer_id: str, date: str, time_slot: str, inspection_type: str) -> dict:
    problem = booking_problem(date, inspection_type)
    if problem:
        return {"error": problem}

    taken = await db.pool.fetchval(
        "SELECT 1 FROM inspections WHERE date = $1 AND time_slot = $2 AND status = 'confirmed'", date, time_slot
    )
    if taken:
        return {"error": "That slot is already booked. Choose a different one."}

    booking_id = await db.pool.fetchval("SELECT 'B' || lpad(nextval('booking_ids')::text, 6, '0')")
    await db.pool.execute(
        "INSERT INTO inspections (id, customer_id, type, date, time_slot) VALUES ($1, $2, $3, $4, $5)",
        booking_id,
        customer_id,
        inspection_type,
        date,
        time_slot,
    )
    return {"booking_id": booking_id, "date": date, "time_slot": time_slot}


async def cancel_inspection(booking_id: str) -> dict:
    booking = await db.pool.fetchrow(
        "SELECT date, time_slot FROM inspections WHERE id = $1 AND status = 'confirmed'", booking_id
    )
    if not booking:
        return {"error": f"There is no active booking {booking_id}."}

    await db.pool.execute("UPDATE inspections SET status = 'cancelled' WHERE id = $1", booking_id)

    # Cancelling within 24 hours of the start costs $50.
    start = datetime.fromisoformat(f"{booking['date']}T{booking['time_slot'][:5]}")
    hours_until = (start - datetime.now()).total_seconds() / 3600
    return {"cancelled": booking_id, "late_fee_usd": 50 if 0 < hours_until < 24 else 0}


TOOLS = {
    "lookup_customer": lookup_customer,
    "check_availability": check_availability,
    "book_inspection": book_inspection,
    "cancel_inspection": cancel_inspection,
}


async def run_tool(name: str, args: dict) -> dict:
    tool = TOOLS.get(name)
    if not tool:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await tool(**args)
    except Exception as error:
        return {"error": f"Internal error: {error}"}
