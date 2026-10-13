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
    # TODO FI: palauta artistin esiintymiset: event_id, day, stage, starts. Tuntematon id → 404.
    # TODO EN: return the artist's performances: event_id, day, stage, starts. Unknown id → 404.
    return jsonify(error="not implemented"), 501


@app.get("/api/timetable")
def get_timetable():
    day = request.args.get("day")  # FI: kyselyparametri ?day=2025-07-05 / EN: query parameter
    # TODO FI: rivit {date, stage, artist, starts, ends} aikajärjestyksessä. Ilman parametria koko ohjelma,
    #          virheellinen päivämäärä → 400. Parametrisoi kysely!
    # TODO EN: rows {date, stage, artist, starts, ends} in time order. No parameter → whole program,
    #          invalid date → 400. Parameterize the query!
    return jsonify(error="not implemented"), 501


@app.post("/api/events")
def create_event():
    body = request.get_json(silent=True) or {}
    # TODO FI: tarkista kentät artist_id, stage_id, day_id, start_dt → puuttuu = 400.
    #          Lisää rivi Event-tauluun (event_type 'performance', kesto esim. 45 min).
    #          sqlite3.IntegrityError (esim. olematon artist_id) → 400 ja selkeä virheviesti.
    #          Onnistuminen → 201 ja uuden rivin tiedot JSONina (sis. event_id).
    # TODO EN: validate artist_id, stage_id, day_id, start_dt → missing = 400.
    #          Insert into Event (event_type 'performance', duration e.g. 45 min).
    #          sqlite3.IntegrityError (e.g. unknown artist_id) → 400 with a clear message.
    #          Success → 201 with the new row as JSON (incl. event_id).
    return jsonify(error="not implemented"), 501


@app.delete("/api/events/<int:event_id>")
def delete_event(event_id):
    # TODO FI: poista esiintyminen. Onnistuminen → 204 (tyhjä runko), tuntematon id → 404.
    # TODO EN: delete the event. Success → 204 (empty body), unknown id → 404.
    return jsonify(error="not implemented"), 501


if __name__ == "__main__":
    # FI: Paikallinen kehityspalvelin. Rahdissa sovellusta ajaa gunicorn (ks. Dockerfile).
    # EN: Local dev server. On Rahti the app is run by gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
