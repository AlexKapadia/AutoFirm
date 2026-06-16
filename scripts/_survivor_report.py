"""Temp survivor reporter (DELETE after use)."""
import sqlite3
import sys

c = sqlite3.connect(".mutmut-cache")
q = (
    "SELECT sf.filename, COUNT(*), "
    "SUM(CASE WHEN m.status='ok_killed' THEN 1 ELSE 0 END), "
    "SUM(CASE WHEN m.status='untested' THEN 1 ELSE 0 END) "
    "FROM Mutant m JOIN Line l ON m.line=l.id "
    "JOIN SourceFile sf ON l.sourcefile=sf.id "
    "GROUP BY sf.filename ORDER BY sf.filename"
)
for fn, total, killed, untested in c.execute(q).fetchall():
    surv = total - killed
    print(f"{killed}/{total} killed  survivors={surv} (untested={untested})  {fn}")

print("\n--- SURVIVORS (mutant_id\tline_no\tstatus\tfile) ---")
pat = sys.argv[1] if len(sys.argv) > 1 else ""
q2 = (
    "SELECT m.id, l.line_number, m.status, sf.filename FROM Mutant m "
    "JOIN Line l ON m.line=l.id JOIN SourceFile sf ON l.sourcefile=sf.id "
    "WHERE m.status NOT IN ('ok_killed','skipped','untested') "
    "AND sf.filename LIKE ? ORDER BY sf.filename, l.line_number"
)
for mid, ln, st, fn in c.execute(q2, (f"%{pat}%",)).fetchall():
    short = fn.split("audit", 1)[-1]
    print(f"{mid}\t{ln}\t{st}\taudit{short}")
