"""What the agents are told about each tool. retell/setup.py and vapi/setup.py send these to the platforms."""

from tools import VALID_TYPES

INSPECTION_TYPE = {"type": "string", "enum": VALID_TYPES, "description": "Type of inspection"}
DATE = {"type": "string", "description": "Date in YYYY-MM-DD"}

TOOL_DEFINITIONS = [
    {
        "name": "lookup_customer",
        "description": "Look up a customer by phone number, name or company. Returns their details, upcoming inspections and a summary of their stores. Call this before booking or cancelling.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Phone number, e.g. 555-0101"},
                "name": {"type": "string", "description": "Full name"},
                "company": {"type": "string", "description": "Company name"},
            },
            "required": [],
        },
    },
    {
        "name": "check_availability",
        "description": "List the open inspection slots for a weekday. Slots are 2 hours, between 8 AM and 5 PM Eastern.",
        "parameters": {
            "type": "object",
            "properties": {"date": DATE, "inspection_type": INSPECTION_TYPE},
            "required": ["date", "inspection_type"],
        },
    },
    {
        "name": "book_inspection",
        "description": "Book an inspection in a slot that check_availability returned. Confirm the details with the caller first. Returns the booking ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID from lookup_customer, e.g. C001"},
                "date": DATE,
                "time_slot": {"type": "string", "description": "Slot from check_availability, e.g. 08:00-10:00"},
                "inspection_type": INSPECTION_TYPE,
            },
            "required": ["customer_id", "date", "time_slot", "inspection_type"],
        },
    },
    {
        "name": "cancel_inspection",
        "description": "Cancel a booking by its ID (from lookup_customer). Cancelling within 24 hours of the inspection costs $50.",
        "parameters": {
            "type": "object",
            "properties": {"booking_id": {"type": "string", "description": "Booking ID, e.g. B001004"}},
            "required": ["booking_id"],
        },
    },
]
