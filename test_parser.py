import dateparser
from datetime import datetime

text = "Book a meeting tomorrow at 11 PM"

parsed = dateparser.parse(
    text,
    settings={
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now()
    }
)

print("Parsed:", parsed)
