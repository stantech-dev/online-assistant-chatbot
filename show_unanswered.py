import sqlite3

"""Run it to read logs(unanswered.db)"""


conn = sqlite3.connect("logs/unanswered.db")
rows = conn.execute(
    "SELECT asked_at, question, top_score FROM unanswered ORDER BY id DESC LIMIT 50"
).fetchall()
for asked_at, question, score in rows:
    print(f"{asked_at}  [{score:.2f}]  {question}")
print(f"\n{len(rows)} shown")