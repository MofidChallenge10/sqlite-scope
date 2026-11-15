#!/usr/bin/env python3
"""Inspect SQLite schema and row counts using a read-only connection."""
import argparse,json,pathlib,sqlite3,sys,unittest
from urllib.parse import quote
def inspect_database(path):
    resolved=pathlib.Path(path).resolve(); uri="file:"+quote(resolved.as_posix(),safe="/:")+"?mode=ro"
    db=sqlite3.connect(uri,uri=True)
    try:
        tables=[]
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            quoted='"'+name.replace('"','""')+'"'
            cols=[{"name":r[1],"type":r[2],"not_null":bool(r[3]),"primary_key":bool(r[5])} for r in db.execute(f"PRAGMA table_info({quoted})")]
            count=db.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
            tables.append({"name":name,"rows":count,"columns":cols})
        return {"database":str(resolved),"tables":tables}
    finally: db.close()
class Tests(unittest.TestCase):
    def test_read_only_schema(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/"demo.db"; db=sqlite3.connect(p); db.execute("CREATE TABLE notes(id INTEGER PRIMARY KEY, body TEXT NOT NULL)"); db.executemany("INSERT INTO notes(body) VALUES (?)",[("a",),("b",)]); db.commit(); db.close()
            report=inspect_database(p); self.assertEqual(report["tables"][0]["rows"],2); self.assertEqual(report["tables"][0]["columns"][1]["name"],"body")
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("database"); ap.add_argument("--json",action="store_true"); a=ap.parse_args()
    try: report=inspect_database(a.database)
    except (OSError,sqlite3.Error) as exc: ap.error(str(exc))
    if a.json: print(json.dumps(report,indent=2))
    else:
        for table in report["tables"]:
            print(f"{table['name']} · {table['rows']} rows")
            for col in table["columns"]: print(f"  {col['name']}: {col['type'] or 'ANY'}{' · PK' if col['primary_key'] else ''}")
        if not report["tables"]: print("No user tables found.")
if __name__=="__main__":
    if "--self-test" in sys.argv: unittest.main(argv=[sys.argv[0]])
    else: main()
