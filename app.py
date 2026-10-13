"""My Festival REST API — M10 starter (CSC Rahti).

FI: Tämä on M10-tehtävän lähtöpohja. GET /api/artists on valmiina mallina;
    toteuta loput TODO-kohdat. Aja paikallisesti:  python app.py
    ja testaa:  python test_endpoints.py http://localhost:8080
EN: This is the M10 starter. GET /api/artists is done as an example;
    implement the remaining TODOs. Run locally:  python app.py
    and test:  python test_endpoints.py http://localhost:8080
"""
import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)

# FI: Kanta kulkee kontin mukana. Polun voi vaihtaa ympäristömuuttujalla.
# EN: The database ships inside the container. Override the path with an env var.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "myfestival.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # M8: sqlite3 ei valvo FK:ita oletuksena / FKs are off by default
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def health():
    """FI: Rahti ja selain näkevät, että sovellus on pystyssä.
    EN: Lets Rahti and your browser see the app is up."""
    return jsonify(status="ok", endpoints=["/api/artists", "/api/days", "/api/stages",
                                           "/api/artists/<id>/events", "/api/timetable?day=YYYY-MM-DD",
                                           "POST /api/events", "DELETE /api/events/<id>"])


@app.get("/api/artists")
def get_artists():
    conn = get_db()
    rows = conn.execute("SELECT artist_id, name, country FROM Artist ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.get("/api/days")
def get_days():
    """FI: Apuendpoint: festivaalipäivät (tarkistin hakee tästä day_id:n).
    EN: Helper endpoint: festival days (the checker reads day_id from here)."""
    conn = get_db()
    rows = conn.execute("SELECT day_id, date FROM Day ORDER BY date").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.get("/api/stages")
def get_stages():
    """FI: Apuendpoint: lavat. EN: Helper endpoint: stages."""
    conn = get_db()
    rows = conn.execute("SELECT stage_id, name FROM Stage ORDER BY stage_id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.get("/api/artists/<int:artist_id>/events")
def get_artist_events(artist_id):
    """Return performances for one artist; unknown artist ids return 404."""
    conn = get_db()
    artist = conn.execute(
        "SELECT artist_id FROM Artist WHERE artist_id = ?", (artist_id,)
    ).fetchone()
    if artist is None:
        conn.close()
        return jsonify(error="Artist not found"), 404

    rows = conn.execute(
        """
        SELECT e.event_id, d.date AS day, s.name AS stage,
               e.start_dt AS starts
        FROM Event AS e
        JOIN Day AS d ON d.day_id = e.day_id
        JOIN Stage AS s ON s.stage_id = e.stage_id
        JOIN EventType AS et ON et.event_type_id = e.event_type_id
        WHERE e.artist_id = ? AND et.code = 'performance'
        ORDER BY e.start_dt, s.name
        """,
        (artist_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.get("/api/timetable")
def get_timetable():
    day = request.args.get("day")
    if day is not None:
        # Require a real calendar date in YYYY-MM-DD format.
        try:
            from datetime import date
            parsed_day = date.fromisoformat(day)
            if parsed_day.isoformat() != day:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify(error="day must be a valid YYYY-MM-DD date"), 400

    sql = """
        SELECT d.date AS date, s.name AS stage, a.name AS artist,
               e.start_dt AS starts, e.end_dt AS ends
        FROM Event AS e
        JOIN Day AS d ON d.day_id = e.day_id
        JOIN Stage AS s ON s.stage_id = e.stage_id
        JOIN Artist AS a ON a.artist_id = e.artist_id
        JOIN EventType AS et ON et.event_type_id = e.event_type_id
        WHERE et.code = 'performance'
    """
    params = ()
    if day is not None:
        sql += " AND d.date = ?"
        params = (day,)
    sql += " ORDER BY e.start_dt, s.name"

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.post("/api/events")
def create_event():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    required = ("artist_id", "stage_id", "day_id", "start_dt")
    missing = [key for key in required if key not in body or body[key] in (None, "")]
    if missing:
        return jsonify(error="Missing required fields: " + ", ".join(missing)), 400

    # IDs must be integers (not booleans).
    ids = {}
    for key in ("artist_id", "stage_id", "day_id"):
        value = body[key]
        if isinstance(value, bool):
            return jsonify(error=f"{key} must be an integer"), 400
        try:
            converted = int(value)
        except (TypeError, ValueError):
            return jsonify(error=f"{key} must be an integer"), 400
        if str(converted) != str(value).strip():
            return jsonify(error=f"{key} must be an integer"), 400
        ids[key] = converted

    start_dt = body["start_dt"]
    if not isinstance(start_dt, str):
        return jsonify(error="start_dt must use YYYY-MM-DD HH:MM:SS format"), 400
    from datetime import datetime, timedelta
    try:
        parsed_start = datetime.strptime(start_dt, "%Y-%m-%d %H:%M:%S")
        if parsed_start.strftime("%Y-%m-%d %H:%M:%S") != start_dt:
            raise ValueError
    except ValueError:
        return jsonify(error="start_dt must use YYYY-MM-DD HH:MM:SS format"), 400

    conn = get_db()
    try:
        # Ensure the requested day exists and matches the date in start_dt.
        day_row = conn.execute(
            "SELECT date FROM Day WHERE day_id = ?", (ids["day_id"],)
        ).fetchone()
        if day_row is None:
            return jsonify(error="Unknown day_id"), 400
        if str(day_row["date"]) != parsed_start.date().isoformat():
            return jsonify(error="start_dt date must match day_id"), 400

        cursor = conn.execute(
            "SELECT event_type_id FROM EventType WHERE code = 'performance'"
        )
        event_type = cursor.fetchone()
        if event_type is None:
            return jsonify(error="EventType 'performance' is missing"), 500

        end_dt = parsed_start + timedelta(minutes=45)
        cur = conn.execute(
            """
            INSERT INTO Event
                (event_type_id, day_id, stage_id, artist_id, start_dt, end_dt, duration_min)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type["event_type_id"], ids["day_id"], ids["stage_id"],
                ids["artist_id"], parsed_start.strftime("%Y-%m-%d %H:%M:%S"),
                end_dt.strftime("%Y-%m-%d %H:%M:%S"), 45,
            ),
        )
        event_id = cur.lastrowid
        conn.commit()
        return jsonify(
            event_id=event_id,
            artist_id=ids["artist_id"],
            stage_id=ids["stage_id"],
            day_id=ids["day_id"],
            start_dt=parsed_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            duration_min=45,
        ), 201
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return jsonify(error=f"Invalid event data: {exc}"), 400
    finally:
        conn.close()


@app.delete("/api/events/<int:event_id>")
def delete_event(event_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM Event WHERE event_id = ?", (event_id,))
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify(error="Event not found"), 404
        conn.commit()
        return "", 204
    finally:
        conn.close()


if __name__ == "__main__":
    # FI: Paikallinen kehityspalvelin. Rahdissa sovellusta ajaa gunicorn (ks. Dockerfile).
    # EN: Local dev server. On Rahti the app is run by gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
