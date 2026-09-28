"""Data-quality profile of the Kaggle "Smart meters in London" dataset.

Reads the CSVs in place with DuckDB. Nothing under datasets/ is written; intermediate
tables live in a throwaway DuckDB file in the system temp directory.
Prints a Markdown summary and saves it to checks/profile_report.md.

Run from anywhere:
    uv run --group dev python checks/profile_data.py
"""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets"
HH_GLOB = DATA / "halfhourly_dataset" / "*.csv"
WEATHER_CSV = DATA / "weather_hourly_darksky.csv"
INFO_CSV = DATA / "informations_households.csv"
REPORT_PATH = Path(__file__).resolve().parent / "profile_report.md"

# Thresholds
ZERO_RUN_SLOTS = 48  # one full day of consecutive zero readings
OUTLIER_P99_MULT = 10  # reading > 10x the household's own 99th percentile
SUPPLY_LIMIT_KWH = 11.5  # 100 A x 230 V for 30 min: ceiling for a standard UK home supply
MAX_LIST_ROWS = 40

# A timestamp is on the half-hour grid only if the raw text is exactly HH:00 or HH:30 with
# zero seconds and zero fractional digits. The raw text is checked because DuckDB truncates
# the 7th fractional digit when casting to TIMESTAMP.
GRID_REGEX = r"\d{4}-\d{2}-\d{2} \d{2}:(00|30):00(\.0+)?"

# Figures from the earlier analysis, to cross-check.
EXPECTED = {
    "rows": 167_817_021,
    "households": 5_561,
    "null_strings": 5_560,
    "duplicates": 0,
    "missing_pct": 0.27,
    "first_min": date(2011, 11, 23),
    "first_max": date(2013, 10, 30),
    "last_min": date(2012, 5, 22),
    "last_max": date(2014, 2, 28),
}


def lit(value: object) -> str:
    """Render a Python value as a SQL literal."""
    if isinstance(value, Path):
        value = value.as_posix()
    if isinstance(value, datetime):
        return f"TIMESTAMP '{value.isoformat(sep=' ')}'"
    return "'" + str(value).replace("'", "''") + "'"


def fmt(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".") if value == value else "NaN"
    return str(value)


def pct(part: float, whole: float, digits: int = 2) -> str:
    return f"{100 * part / whole:.{digits}f}%" if whole else "—"


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.findings: list[str] = []

    def h(self, text: str, level: int = 2) -> None:
        self.lines += ["", "#" * level + " " + text, ""]

    def p(self, text: str = "") -> None:
        self.lines.append(text)

    def kv(self, rows: list[tuple[str, object]]) -> None:
        self.table(["Metric", "Value"], rows)

    def table(self, headers: list[str], rows: list[tuple], limit: int | None = None) -> None:
        shown = rows if limit is None else rows[:limit]
        self.lines.append("| " + " | ".join(headers) + " |")
        self.lines.append("|" + "|".join("---" for _ in headers) + "|")
        for row in shown:
            cells = [fmt(c).replace("|", "\\|") for c in row]
            self.lines.append("| " + " | ".join(cells) + " |")
        if not rows:
            self.lines.append("| " + " | ".join("(none)" if i == 0 else "" for i in range(len(headers))) + " |")
        if limit is not None and len(rows) > limit:
            self.lines.append(f"\n_…{len(rows) - limit:,} more rows not shown._")
        self.lines.append("")

    def finding(self, text: str) -> None:
        self.findings.append(text)

    def render(self, header: list[str]) -> str:
        top = header + ["", "## Key findings", ""] + [f"- {f}" for f in self.findings]
        return "\n".join(top + self.lines) + "\n"


def log(msg: str, start: float) -> None:
    print(f"[{time.perf_counter() - start:7.1f}s] {msg}", file=sys.stderr, flush=True)


def one(con: duckdb.DuckDBPyConnection, sql: str) -> tuple:
    return con.execute(sql).fetchone()


def rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[tuple]:
    return con.execute(sql).fetchall()


def last_sunday(year: int, month: int) -> date:
    d = date(year, month, 31)  # March and October both have 31 days
    return d - timedelta(days=(d.weekday() + 1) % 7)


def dst_note(ts: datetime) -> str:
    d = ts.date()
    if d == last_sunday(d.year, 3):
        return "UK clocks go forward"
    if d == last_sunday(d.year, 10):
        return "UK clocks go back"
    return ""


def main() -> None:
    start = time.perf_counter()
    for path in (WEATHER_CSV, INFO_CSV):
        if not path.exists():
            sys.exit(f"Missing input: {path}")
    if not any(HH_GLOB.parent.glob("*.csv")):
        sys.exit(f"No CSVs found at {HH_GLOB}")

    r = Report()
    tmp = tempfile.TemporaryDirectory(prefix="smart_meter_profile_", ignore_cleanup_errors=True)
    con = duckdb.connect(str(Path(tmp.name) / "profile.duckdb"))
    try:
        con.execute(f"SET temp_directory = {lit(Path(tmp.name) / 'spill')}")
        con.execute("SET preserve_insertion_order = false")
        run_checks(con, r, start)
    finally:
        con.close()
        tmp.cleanup()

    n_files = len(list(HH_GLOB.parent.glob("*.csv")))
    header = [
        "# Smart meters in London: data-quality profile",
        "",
        f"- Generated: {datetime.now():%Y-%m-%d %H:%M} by `checks/profile_data.py`",
        f"- DuckDB {duckdb.__version__}; runtime {time.perf_counter() - start:,.0f}s",
        f"- Inputs: `datasets/halfhourly_dataset/*.csv` ({n_files} files), "
        "`datasets/weather_hourly_darksky.csv`, `datasets/informations_households.csv`",
    ]
    text = r.render(header)
    REPORT_PATH.write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    log(f"Report written to {REPORT_PATH}", start)


def run_checks(con: duckdb.DuckDBPyConnection, r: Report, start: float) -> None:
    cross: dict[str, object] = {}

    # ------------------------------------------------------------------ load
    log("Sniffing column types", start)
    sniffed = rows(con, f"DESCRIBE SELECT * FROM read_csv({lit(HH_GLOB)})")

    log("Loading half-hourly readings (all columns as text)", start)
    con.execute(f"""
        CREATE TABLE hh AS
        SELECT
            LCLid,
            ts,
            ts IS NOT NULL AND regexp_full_match(tstp, {lit(GRID_REGEX)}) AS on_grid,
            CASE WHEN ts IS NULL THEN tstp END AS bad_tstp,
            val,
            CASE WHEN val IS NULL OR NOT isfinite(val)
                 THEN coalesce(energy, '<empty field>') END AS bad_val
        FROM (
            SELECT
                LCLid, tstp, energy,
                try_cast(tstp AS TIMESTAMP) AS ts,
                try_cast(trim(energy) AS DOUBLE) AS val
            FROM read_csv({lit(HH_GLOB)}, header = true, all_varchar = true,
                          names = ['LCLid', 'tstp', 'energy'])
        )
    """)

    # ------------------------------------------------------------------ 1. basics
    log("1. Row counts, types, non-numeric values", start)
    r.h("1. Half-hourly readings: size, types, unparseable values")
    (n_rows, n_hh, null_id, bad_id, bad_ts, non_num, non_finite, null_str) = one(con, f"""
        SELECT count(*), count(DISTINCT LCLid),
               count(*) FILTER (LCLid IS NULL),
               count(*) FILTER (NOT regexp_full_match(LCLid, 'MAC\\d{{6}}')),
               count(*) FILTER (ts IS NULL),
               count(*) FILTER (val IS NULL),
               count(*) FILTER (val IS NOT NULL AND NOT isfinite(val)),
               count(*) FILTER (trim(bad_val) = 'Null')
        FROM hh
    """)
    cross.update(rows=n_rows, households=n_hh, null_strings=null_str)
    r.kv([
        ("Rows", n_rows),
        ("Distinct households (LCLid)", n_hh),
        ("Rows with NULL LCLid", null_id),
        ("Rows whose LCLid is not `MAC` + 6 digits", bad_id),
        ("Rows whose `tstp` does not parse as a timestamp", bad_ts),
        ("Rows whose energy value is not numeric after trimming", non_num),
        ("Rows whose energy parses to NaN/Infinity", non_finite),
    ])
    r.p("Types DuckDB infers when reading `halfhourly_dataset/*.csv` with default sniffing:")
    r.p()
    r.table(["Column", "Inferred type"], [(c[0], c[1]) for c in sniffed])
    energy_type = next((c[1] for c in sniffed if c[0].startswith("energy")), "?")
    if energy_type != "DOUBLE":
        r.finding(f"`energy(kWh/hh)` is read as **{energy_type}**, not a number; values are "
                  "whitespace-padded (e.g. `' 0 '`) and include non-numeric strings.")

    bad_vals = rows(con, """
        SELECT bad_val, trim(bad_val), count(*) AS n, count(DISTINCT LCLid)
        FROM hh WHERE bad_val IS NOT NULL GROUP BY bad_val ORDER BY n DESC
    """)
    r.p()
    r.p("All energy values that don't convert to a finite number after trimming (raw value shown with `repr` to reveal whitespace):")
    r.p()
    r.table(["Raw value", "Trimmed", "Rows", "Households"],
            [(repr(v), repr(t), n, h) for v, t, n, h in bad_vals], limit=MAX_LIST_ROWS)
    if non_num:
        r.finding(f"{non_num:,} energy values don't parse as numbers "
                  f"({', '.join(repr(t) for _, t, _, _ in bad_vals[:5])}).")
    if bad_ts:
        examples = rows(con, "SELECT DISTINCT bad_tstp FROM hh WHERE bad_tstp IS NOT NULL LIMIT 10")
        r.p("Examples of unparseable timestamps: " + ", ".join(repr(e[0]) for e in examples))
        r.finding(f"{bad_ts:,} timestamps don't parse.")

    # ------------------------------------------------------------------ 2. off-grid
    log("2. Off-grid timestamps", start)
    r.h("2. Rows off the half-hour grid")
    r.p("Off-grid means the timestamp isn't exactly `HH:00:00` or `HH:30:00` "
        "(checked on the raw text, fractional digits included), or doesn't parse at all.")
    r.p()
    off_n, off_null, off_num = one(con, """
        SELECT count(*), count(*) FILTER (val IS NULL), count(*) FILTER (val IS NOT NULL)
        FROM hh WHERE NOT on_grid
    """)
    r.kv([
        ("Off-grid rows", off_n),
        ("…with a non-numeric (e.g. Null) value", off_null),
        ("…with a numeric value", off_num),
        ("Non-numeric values that ARE on the grid", non_num - off_null),
    ])
    if off_n:
        times = rows(con, """
            SELECT strftime(ts, '%M:%S.%f') AS mm_ss, count(*) AS n
            FROM hh WHERE NOT on_grid AND ts IS NOT NULL GROUP BY 1 ORDER BY n DESC LIMIT 10
        """)
        r.p("Most common minute:second parts of off-grid timestamps:")
        r.p()
        r.table(["mm:ss.ffffff", "Rows"], times)
        by_date = rows(con, """
            SELECT ts::DATE AS d, count(*), count(*) FILTER (val IS NULL),
                   count(*) FILTER (val IS NOT NULL), count(DISTINCT LCLid)
            FROM hh WHERE NOT on_grid GROUP BY d ORDER BY d
        """)
        r.p(f"Distribution by date ({len(by_date):,} distinct dates):")
        r.p()
        r.table(["Date", "Rows", "Non-numeric", "Numeric", "Households"], by_date, limit=MAX_LIST_ROWS)
        r.finding(f"{off_n:,} rows are off the half-hour grid ({off_null:,} non-numeric, "
                  f"{off_num:,} numeric) across {len(by_date):,} dates.")

    # ------------------------------------------------------------------ 3. duplicates
    log("3. Duplicates on (LCLid, tstp)", start)
    r.h("3. Duplicate (LCLid, tstp) pairs")
    dup_keys, dup_extra, dup_conflict = one(con, """
        SELECT count(*), coalesce(sum(n - 1), 0), count(*) FILTER (nv > 1)
        FROM (SELECT LCLid, ts, count(*) AS n, count(DISTINCT val) AS nv
              FROM hh WHERE ts IS NOT NULL GROUP BY LCLid, ts HAVING count(*) > 1)
    """)
    cross["duplicates"] = dup_keys
    r.kv([
        ("(LCLid, tstp) keys appearing more than once", dup_keys),
        ("Surplus rows (rows beyond the first per key)", dup_extra),
        ("Duplicate keys whose values disagree", dup_conflict),
    ])
    if dup_keys:
        r.finding(f"{dup_keys:,} duplicated (LCLid, tstp) keys ({dup_conflict:,} with conflicting values).")

    # One row per on-grid slot. Deduplicate only if needed; otherwise a view avoids a copy.
    if dup_keys:
        con.execute("""CREATE TABLE slots AS SELECT LCLid, ts, max(val) AS val
                       FROM hh WHERE on_grid GROUP BY LCLid, ts""")
    else:
        con.execute("CREATE VIEW slots AS SELECT LCLid, ts, val FROM hh WHERE on_grid")

    # ------------------------------------------------------------------ 4. gaps
    log("4. Missing half-hour slots", start)
    r.h("4. Missing half-hour slots per household")
    r.p("Expected slots = every half hour from the household's first to last on-grid reading, inclusive. "
        "A slot counts as present if any row exists for it, even a `Null` one.")
    r.p()
    con.execute("""
        CREATE TABLE hh_span AS
        SELECT LCLid, min(ts) AS first_ts, max(ts) AS last_ts,
               count(*) AS present,
               count(*) FILTER (isfinite(val)) AS valued,
               date_diff('minute', min(ts), max(ts)) // 30 + 1 AS expected
        FROM slots GROUP BY LCLid
    """)
    con.execute("""
        CREATE TABLE gaps AS
        SELECT LCLid, prev_ts + INTERVAL 30 MINUTE AS first_missing,
               date_diff('minute', prev_ts, ts) // 30 - 1 AS missing_slots
        FROM (SELECT LCLid, ts, lag(ts) OVER (PARTITION BY LCLid ORDER BY ts) AS prev_ts FROM slots)
        WHERE date_diff('minute', prev_ts, ts) > 30
    """)
    exp_total, present_total, valued_total, hh_with_gaps, span_hh = one(con, """
        SELECT sum(expected), sum(present), sum(valued),
               count(*) FILTER (present < expected), count(*) FROM hh_span
    """)
    missing_total = exp_total - present_total
    n_gaps, gap_slots, gap_median, gap_max = one(con, """
        SELECT count(*), coalesce(sum(missing_slots), 0), median(missing_slots), max(missing_slots) FROM gaps
    """)
    assert gap_slots == missing_total, f"gap sum {gap_slots} != expected-present {missing_total}"
    missing_pct = 100 * missing_total / exp_total
    cross["missing_pct"] = missing_pct
    hh_all_null = one(con, "SELECT count(*) FROM hh_span WHERE valued = 0")[0]
    r.kv([
        ("Households with at least one on-grid reading", span_hh),
        ("Expected slots (sum over households)", exp_total),
        ("Present slots", present_total),
        ("Missing slots", missing_total),
        ("Missing %", f"{missing_pct:.4f}%"),
        ("Missing % counting Null-valued slots as missing", pct(exp_total - valued_total, exp_total, 4)),
        ("Households with ≥1 gap", f"{hh_with_gaps:,} ({pct(hh_with_gaps, span_hh)})"),
        ("Households whose values are all non-numeric", hh_all_null),
        ("Number of gaps (runs of missing slots)", n_gaps),
        ("Median gap length (slots)", gap_median),
        ("Longest gap (slots)", f"{fmt(gap_max)} ({gap_max / 48:,.1f} days)" if gap_max else "—"),
    ])
    no_valid = rows(con, """
        SELECT LCLid, count(*), min(ts), any_value(bad_val) FROM hh
        WHERE LCLid NOT IN (SELECT LCLid FROM hh_span) GROUP BY LCLid ORDER BY LCLid
    """)
    cross["households_on_grid"] = span_hh
    if no_valid:
        r.p(f"{len(no_valid):,} household IDs have no on-grid reading at all, so they drop out of every "
            "per-household check below:")
        r.p()
        r.table(["LCLid", "Rows", "Timestamp", "Value"], [(i, n, t, repr(v)) for i, n, t, v in no_valid])
        r.finding(f"{len(no_valid):,} household IDs appear only in off-grid `Null` rows (no usable data): "
                  + ", ".join(f"`{i}`" for i, *_ in no_valid) + ".")
    gap_dist = rows(con, """
        SELECT CASE WHEN missing_slots = 1 THEN '1 slot (30 min)'
                    WHEN missing_slots <= 5 THEN '2–5 slots (≤2.5 h)'
                    WHEN missing_slots < 48 THEN '6–47 slots (<1 day)'
                    WHEN missing_slots < 336 THEN '48–335 slots (1 day to <1 week)'
                    WHEN missing_slots < 1440 THEN '336–1,439 slots (1 week to <30 days)'
                    ELSE '≥1,440 slots (30+ days)' END AS bucket,
               min(missing_slots) AS k, count(*), count(DISTINCT LCLid), sum(missing_slots)
        FROM gaps GROUP BY bucket ORDER BY k
    """)
    r.p("Gap length distribution:")
    r.p()
    r.table(["Gap length", "Gaps", "Households", "Missing slots", "% of all missing"],
            [(b, g, h, s, pct(s, missing_total)) for b, _, g, h, s in gap_dist])
    shared = rows(con, """
        SELECT first_missing, count(*) AS households, min(missing_slots), max(missing_slots)
        FROM gaps GROUP BY first_missing ORDER BY households DESC, first_missing LIMIT 10
    """)
    r.p("Gap start times shared by the most households (hints at system-wide outages rather than single meters):")
    r.p()
    r.table(["First missing slot", "Households", "Min length", "Max length"], shared)
    if missing_total:
        r.finding(f"{missing_pct:.2f}% of expected half-hour slots are missing; {hh_with_gaps:,} of "
                  f"{span_hh:,} households have gaps (longest: {gap_max:,} slots ≈ {gap_max / 48:,.0f} days).")

    # ------------------------------------------------------------------ 5. coverage
    log("5. Coverage", start)
    r.h("5. Coverage: first and last reading dates")
    cov = one(con, """
        SELECT quantile_disc(first_ts::DATE, [0, 0.25, 0.5, 0.75, 1]),
               quantile_disc(last_ts::DATE, [0, 0.25, 0.5, 0.75, 1])
        FROM hh_span
    """)
    firsts, lasts = cov
    cross.update(first_min=firsts[0], first_max=firsts[4], last_min=lasts[0], last_max=lasts[4])
    r.table(["", "Min", "25%", "Median", "75%", "Max"],
            [("First reading", *firsts), ("Last reading", *lasts)])
    # Same, but counting every row (including off-grid and Null rows)
    raw_span = one(con, """
        SELECT min(f), max(f), min(l), max(l) FROM (
            SELECT min(ts)::DATE AS f, max(ts)::DATE AS l FROM hh WHERE ts IS NOT NULL GROUP BY LCLid)
    """)
    if raw_span != (firsts[0], firsts[4], lasts[0], lasts[4]):
        r.p(f"Counting all rows (off-grid included), first readings range {raw_span[0]} to {raw_span[1]} "
            f"and last readings {raw_span[2]} to {raw_span[3]}.")
        r.p()
    span_buckets = one(con, """
        SELECT count(*) FILTER (days < 30), count(*) FILTER (days < 180), count(*) FILTER (days < 365),
               count(*) FILTER (last_ts::DATE = (SELECT max(last_ts)::DATE FROM hh_span))
        FROM (SELECT *, date_diff('day', first_ts, last_ts) AS days FROM hh_span)
    """)
    r.kv([
        ("Households covering < 30 days", span_buckets[0]),
        ("Households covering < 180 days", span_buckets[1]),
        ("Households covering < 365 days", span_buckets[2]),
        ("Households still reporting on the final date", span_buckets[3]),
    ])
    monthly = rows(con, """
        WITH f AS (SELECT strftime(first_ts, '%Y-%m') AS m, count(*) AS n FROM hh_span GROUP BY 1),
             l AS (SELECT strftime(last_ts, '%Y-%m') AS m, count(*) AS n FROM hh_span GROUP BY 1)
        SELECT m, coalesce(f.n, 0), coalesce(l.n, 0) FROM f FULL OUTER JOIN l USING (m) ORDER BY m
    """)
    r.p("Households by month of first and last reading:")
    r.p()
    r.table(["Month", "First readings", "Last readings"], monthly)
    r.finding(f"Coverage is staggered: first readings span {firsts[0]} to {firsts[4]}, last readings "
              f"{lasts[0]} to {lasts[4]}; {span_buckets[2]:,} households cover less than a year.")

    # ------------------------------------------------------------------ 6. values
    log("6. Value problems", start)
    r.h("6. Value problems")
    n_num, n_neg, hh_neg, n_zero, vmin, vmax, q = one(con, """
        SELECT count(*), count(*) FILTER (val < 0), count(DISTINCT LCLid) FILTER (val < 0),
               count(*) FILTER (val = 0), min(val), max(val),
               quantile_cont(val, [0.5, 0.9, 0.99, 0.999])
        FROM hh WHERE isfinite(val)
    """)
    r.kv([
        ("Numeric readings", n_num),
        ("Negative readings", f"{n_neg:,} ({hh_neg:,} households)"),
        ("Exact zeros", f"{n_zero:,} ({pct(n_zero, n_num)} of numeric readings)"),
        ("Min / max (kWh per half hour)", f"{fmt(vmin)} / {fmt(vmax)}"),
        ("Median / p90 / p99 / p99.9", " / ".join(fmt(x) for x in q)),
    ])
    if n_neg:
        r.finding(f"{n_neg:,} negative readings in {hh_neg:,} households.")
    zero_hh = one(con, """
        SELECT count(*) FILTER (z = n), count(*) FILTER (z > 0.5 * n)
        FROM (SELECT count(*) AS n, count(*) FILTER (val = 0) AS z FROM hh WHERE isfinite(val) GROUP BY LCLid)
    """)
    r.p(f"Households whose readings are all zero: {zero_hh[0]:,}; more than half zero: {zero_hh[1]:,}.")

    r.h("Consecutive zero runs", 3)
    r.p("A run is consecutive half-hour slots all reading exactly 0; a missing slot or a non-zero/Null reading ends it.")
    r.p()
    con.execute("""
        CREATE TABLE zero_runs AS
        SELECT LCLid, min(ts) AS start_ts, max(ts) AS end_ts, count(*) AS len
        FROM (SELECT LCLid, ts,
                     date_diff('minute', TIMESTAMP '2000-01-01', ts) // 30
                       - row_number() OVER (PARTITION BY LCLid ORDER BY ts) AS grp
              FROM slots WHERE val = 0)
        GROUP BY LCLid, grp
    """)
    zr = one(con, f"""
        SELECT count(*) FILTER (len >= {ZERO_RUN_SLOTS}),
               count(DISTINCT LCLid) FILTER (len >= {ZERO_RUN_SLOTS}),
               count(DISTINCT LCLid) FILTER (len >= 336),
               count(DISTINCT LCLid) FILTER (len >= 1440),
               coalesce(sum(len) FILTER (len >= {ZERO_RUN_SLOTS}), 0)
        FROM zero_runs
    """)
    r.kv([
        (f"Zero runs of ≥{ZERO_RUN_SLOTS} slots (a full day)", zr[0]),
        (f"Households with a ≥{ZERO_RUN_SLOTS}-slot zero run", f"{zr[1]:,} ({pct(zr[1], n_hh)})"),
        ("Households with a zero run of ≥1 week", zr[2]),
        ("Households with a zero run of ≥30 days", zr[3]),
        ("Readings inside day-plus zero runs", zr[4]),
    ])
    longest = rows(con, """
        SELECT LCLid, start_ts, end_ts, len, round(len / 48, 1) FROM zero_runs ORDER BY len DESC LIMIT 10
    """)
    r.p("Longest zero runs:")
    r.p()
    r.table(["LCLid", "Start", "End", "Slots", "Days"], longest)
    if zr[0]:
        r.finding(f"{zr[1]:,} households have at least one run of ≥{ZERO_RUN_SLOTS} consecutive zeros "
                  f"({zr[3]:,} with a month or longer); likely meter faults or empty homes.")

    r.h("Extreme outliers", 3)
    r.p(f"Two rules: (a) a reading above {OUTLIER_P99_MULT}× the household's own 99th percentile; "
        f"(b) a reading above {SUPPLY_LIMIT_KWH} kWh in a half hour, the most a standard "
        "100 A / 230 V home supply can deliver.")
    r.p()
    con.execute("""
        CREATE TABLE hh_q AS
        SELECT LCLid, median(val) AS med, quantile_cont(val, 0.99) AS p99
        FROM hh WHERE isfinite(val) GROUP BY LCLid
    """)
    con.execute(f"""
        CREATE TABLE outliers AS
        SELECT h.LCLid, h.ts, h.val, q.med, q.p99, h.val / q.p99 AS ratio,
               h.val > {OUTLIER_P99_MULT} * q.p99 AS rel, h.val > {SUPPLY_LIMIT_KWH} AS abs
        FROM hh h JOIN hh_q q USING (LCLid)
        WHERE isfinite(h.val) AND ((q.p99 > 0 AND h.val > {OUTLIER_P99_MULT} * q.p99)
                                   OR h.val > {SUPPLY_LIMIT_KWH})
    """)
    o = one(con, """
        SELECT count(*) FILTER (rel), count(DISTINCT LCLid) FILTER (rel),
               count(*) FILTER (abs), count(DISTINCT LCLid) FILTER (abs)
        FROM outliers
    """)
    r.kv([
        (f"Readings > {OUTLIER_P99_MULT}× household p99", f"{o[0]:,} ({o[1]:,} households)"),
        (f"Readings > {SUPPLY_LIMIT_KWH} kWh/hh", f"{o[2]:,} ({o[3]:,} households)"),
    ])
    top = rows(con, """
        SELECT LCLid, ts, val, round(med, 3), round(p99, 3), round(ratio, 1) FROM outliers
        ORDER BY val DESC LIMIT 15
    """)
    r.p("Largest flagged readings:")
    r.p()
    r.table(["LCLid", "Timestamp", "kWh", "Household median", "Household p99", "× p99"], top)
    if o[0] or o[2]:
        r.finding(f"{o[0]:,} readings exceed {OUTLIER_P99_MULT}× their household's p99 ({o[1]:,} households); "
                  f"{o[2]:,} exceed the {SUPPLY_LIMIT_KWH} kWh/hh physical ceiling. Max reading: {fmt(vmax)} kWh.")

    # ------------------------------------------------------------------ 7. weather
    log("7. Weather", start)
    r.h("7. weather_hourly_darksky.csv")
    rng_start, rng_end = one(con, "SELECT min(ts)::DATE, max(ts)::DATE FROM slots")
    w_start = datetime.combine(rng_start, datetime.min.time())
    w_end = datetime.combine(rng_end, datetime.min.time()) + timedelta(hours=23)
    con.execute(f"""
        CREATE TABLE weather AS
        SELECT time AS raw, try_cast(time AS TIMESTAMP) AS t
        FROM read_csv({lit(WEATHER_CSV)}, header = true, all_varchar = true)
    """)
    w_rows, w_bad, w_offhour, w_min, w_max, w_in = one(con, f"""
        SELECT count(*), count(*) FILTER (t IS NULL), count(*) FILTER (t <> date_trunc('hour', t)),
               min(t), max(t), count(*) FILTER (t BETWEEN {lit(w_start)} AND {lit(w_end)})
        FROM weather
    """)
    expected_hours = int((w_end - w_start).total_seconds() // 3600) + 1
    missing_runs = rows(con, f"""
        WITH expected AS (SELECT generate_series AS h
                          FROM generate_series({lit(w_start)}, {lit(w_end)}, INTERVAL 1 HOUR)),
             missing AS (SELECT h FROM expected ANTI JOIN weather ON expected.h = weather.t)
        SELECT min(h), max(h), count(*) FROM (
            SELECT h, date_diff('hour', TIMESTAMP '2000-01-01', h) - row_number() OVER (ORDER BY h) AS grp
            FROM missing)
        GROUP BY grp ORDER BY 1
    """)
    dups = rows(con, f"""
        SELECT t, count(*) FROM weather
        WHERE t BETWEEN {lit(w_start)} AND {lit(w_end)} GROUP BY t HAVING count(*) > 1 ORDER BY t
    """)
    n_missing_hours = sum(n for *_, n in missing_runs)
    r.kv([
        ("Readings date range used", f"{w_start} to {w_end}"),
        ("Weather file time range", f"{w_min} to {w_max}"),
        ("Weather rows (whole file)", w_rows),
        ("Unparseable times", w_bad),
        ("Times not on the hour", w_offhour),
        ("Expected hourly timestamps in range", expected_hours),
        ("Weather rows in range", w_in),
        ("Missing hours", f"{n_missing_hours:,} in {len(missing_runs):,} runs"),
        ("Duplicated timestamps", f"{len(dups):,} ({sum(n - 1 for _, n in dups):,} surplus rows)"),
    ])
    r.p("Missing hours (consecutive hours grouped):")
    r.p()
    r.table(["From", "To", "Hours", "Weekday", "Note"],
            [(a, b, n, f"{a:%a}", dst_note(a)) for a, b, n in missing_runs], limit=MAX_LIST_ROWS)
    r.p("Duplicated timestamps:")
    r.p()
    r.table(["Time", "Rows", "Weekday", "Note"],
            [(t, n, f"{t:%a}", dst_note(t)) for t, n in dups], limit=MAX_LIST_ROWS)
    if n_missing_hours or dups:
        dst_hits = sum(bool(dst_note(a)) for a, _, _ in missing_runs) + sum(bool(dst_note(t)) for t, _ in dups)
        r.finding(f"Weather: {n_missing_hours:,} missing hours and {len(dups):,} duplicated timestamps in the "
                  f"readings' date range ({dst_hits} of these fall on UK clock-change days).")

    # ------------------------------------------------------------------ 8. households
    log("8. Household metadata", start)
    r.h("8. informations_households.csv vs readings")
    con.execute(f"""
        CREATE TABLE info AS
        SELECT LCLid AS raw, trim(LCLid) AS LCLid
        FROM read_csv({lit(INFO_CSV)}, header = true, all_varchar = true)
    """)
    i_rows, i_ids, i_ws = one(con, "SELECT count(*), count(DISTINCT LCLid), count(*) FILTER (raw <> LCLid) FROM info")
    only_info = rows(con, """
        SELECT DISTINCT LCLid FROM info WHERE LCLid NOT IN (SELECT DISTINCT LCLid FROM hh WHERE LCLid IS NOT NULL)
        ORDER BY 1
    """)
    only_read = rows(con, """
        SELECT LCLid, count(*) FROM hh WHERE LCLid NOT IN (SELECT LCLid FROM info WHERE LCLid IS NOT NULL)
        GROUP BY LCLid ORDER BY 1
    """)
    r.kv([
        ("Rows in informations_households.csv", i_rows),
        ("Distinct IDs", i_ids),
        ("IDs with surrounding whitespace", i_ws),
        ("IDs in metadata but with no readings", len(only_info)),
        ("IDs in readings but not in metadata", len(only_read)),
    ])
    r.p("In metadata, no readings: " + (", ".join(f"`{x}`" for (x,) in only_info) or "none"))
    r.p()
    r.p("In readings, not in metadata:")
    r.p()
    r.table(["LCLid", "Rows"], only_read, limit=MAX_LIST_ROWS)
    if only_info or only_read or i_rows != i_ids:
        r.finding(f"Household metadata: {len(only_info):,} IDs have no readings, {len(only_read):,} reading "
                  f"IDs have no metadata, {i_rows - i_ids:,} duplicate metadata rows.")

    # ------------------------------------------------------------------ cross-check
    log("Cross-check", start)
    r.h("9. Cross-check against earlier figures")
    checks = [
        ("Rows", "rows", lambda a, b: a == b),
        ("Households (distinct LCLid, any row)", "households", lambda a, b: a == b),
        ("Households with ≥1 on-grid reading", "households_on_grid", lambda a, b: a == b),
        ("`Null` strings", "null_strings", lambda a, b: a == b),
        ("Duplicate (LCLid, tstp) keys", "duplicates", lambda a, b: a == b),
        ("Missing slots %", "missing_pct", lambda a, b: round(a, 2) == b),
        ("Earliest first reading", "first_min", lambda a, b: a == b),
        ("Latest first reading", "first_max", lambda a, b: a == b),
        ("Earliest last reading", "last_min", lambda a, b: a == b),
        ("Latest last reading", "last_max", lambda a, b: a == b),
    ]
    table, mismatches = [], []
    for label, key, same in checks:
        mine = cross[key]
        expected_key = "households" if key == "households_on_grid" else key
        ok = same(mine, EXPECTED[expected_key])
        shown = f"{mine:.4f}" if isinstance(mine, float) else mine
        table.append((label, EXPECTED[expected_key], shown, "✓ match" if ok else "✗ MISMATCH"))
        if not ok:
            mismatches.append(f"{label} (earlier {fmt(EXPECTED[expected_key])}, now {fmt(shown)})")
    r.table(["Metric", "Earlier", "This run", "Result"], table)
    r.finding("Cross-check: " + ("all earlier figures match." if not mismatches
                                 else "**mismatches** in " + "; ".join(mismatches) + "."))


if __name__ == "__main__":
    main()
