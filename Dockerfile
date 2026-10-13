# My Festival API — CSC Rahti container
# FI: Rahti rakentaa tästä tiedostosta kontin (Import from Git → Dockerfile).
# EN: Rahti builds the container from this file (Import from Git → Dockerfile).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FI: Rahti ajaa kontin satunnaisella käyttäjä-id:llä, joka kuuluu root-ryhmään (0).
#     SQLite tarvitsee kirjoitusoikeuden sekä tiedostoon että kansioon (journal-tiedosto).
# EN: Rahti runs the container with a random user id in the root group (0).
#     SQLite needs write access to both the file and the folder (journal file).
RUN chgrp -R 0 /app && chmod -R g+rwX /app

USER 1001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "app:app"]
