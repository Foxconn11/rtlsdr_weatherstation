#!/usr/bin/env python3

import json
import sys
import time
from typing import Any, Dict, Optional

import mysql.connector
from mysql.connector import Error as MySQLError

from settings import MYSQL_CONFIG, STATION_ID, RADIOACTIVITY_DEFAULT


INSERT_SQL = """
INSERT INTO data (
    timestamp,
    stationid,
    battery,
    temperature,
    humidity,
    winddirection,
    wind_avg,
    wind_max,
    rain_mm,
    radioactivity
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def connect_mysql():
    return mysql.connector.connect(**MYSQL_CONFIG)


def parse_timestamp(timestamp_text: str) -> float:
    return time.mktime(time.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S"))


def get_required(data: Dict[str, Any], key: str) -> Any:
    if key not in data:
        raise KeyError(f"Pflichtfeld fehlt: {key}")
    return data[key]


def print_weather_data(data: Dict[str, Any]) -> None:
    battery_ok = int(get_required(data, "battery_ok"))

    print("Neuer Wetter-Frame empfangen", flush=True)
    print(f"Temperatur: {get_required(data, 'temperature_C')} °C", flush=True)
    print(f"Luftfeuchtigkeit: {get_required(data, 'humidity')} %", flush=True)
    print(f"Windrichtung: {get_required(data, 'wind_dir_deg')} °", flush=True)
    print(f"Windgeschwindigkeit: {get_required(data, 'wind_avg_km_h')} km/h", flush=True)
    print(f"Maximale Windgeschwindigkeit: {get_required(data, 'wind_max_km_h')} km/h", flush=True)
    print(f"Niederschlag: {get_required(data, 'rain_mm')} mm", flush=True)
    print(f"Batteriestand: {'Voll' if battery_ok == 1 else 'Leer'}", flush=True)
    print(f"Zeitstempel des Senders: {get_required(data, 'time')}", flush=True)
    print("", flush=True)


def insert_weather_data(connection, data: Dict[str, Any]) -> None:
    values = (
        get_required(data, "time"),
        get_required(data, "id"),
        get_required(data, "battery_ok"),
        get_required(data, "temperature_C"),
        get_required(data, "humidity"),
        get_required(data, "wind_dir_deg"),
        get_required(data, "wind_avg_km_h"),
        get_required(data, "wind_max_km_h"),
        get_required(data, "rain_mm"),
        RADIOACTIVITY_DEFAULT,
    )

    cursor = connection.cursor()

    try:
        cursor.execute(INSERT_SQL, values)
        connection.commit()

        print(
            f"[OK] Datensatz eingefügt: "
            f"{data['time']} | "
            f"{data['temperature_C']} °C | "
            f"{data['humidity']} % | "
            f"Regenzähler {data['rain_mm']} mm",
            flush=True,
        )

    finally:
        cursor.close()


def ensure_connection(connection):
    if connection is None:
        return connect_mysql()

    try:
        if not connection.is_connected():
            return connect_mysql()
    except MySQLError:
        return connect_mysql()

    return connection


def process_line(connection, line: str, last_timestamp: Optional[float]) -> Optional[float]:
    line = line.strip()

    if not line:
        return last_timestamp

    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        print(f"[WARN] Ungültiges JSON verworfen: {exc}", file=sys.stderr, flush=True)
        return last_timestamp

    try:
        station_id = int(get_required(data, "id"))

        if station_id != STATION_ID:
            return last_timestamp

        timestamp_text = str(get_required(data, "time"))
        timestamp = parse_timestamp(timestamp_text)

        if timestamp == last_timestamp:
            print(
                f"[INFO] Datensatz bereits empfangen, verwerfe Duplikat: {timestamp_text}",
                flush=True,
            )
            return last_timestamp

        print_weather_data(data)
        insert_weather_data(connection, data)

        return timestamp

    except KeyError as exc:
        print(f"[WARN] Frame unvollständig, verworfen: {exc}", file=sys.stderr, flush=True)
        print(f"[WARN] Vorhandene Felder: {list(data.keys())}", file=sys.stderr, flush=True)
        return last_timestamp

    except ValueError as exc:
        print(f"[WARN] Frame enthält ungültige Werte, verworfen: {exc}", file=sys.stderr, flush=True)
        return last_timestamp


def main() -> None:
    print("Auto-RX Wetterstation Receiver gestartet.", flush=True)
    print(f"Filtere auf Station-ID: {STATION_ID}", flush=True)
    print("Warte auf rtl_433 JSON-Daten über STDIN ...", flush=True)
    print("", flush=True)

    connection = None
    last_timestamp: Optional[float] = None

    try:
        connection = connect_mysql()

        for line in sys.stdin:
            try:
                connection = ensure_connection(connection)
                last_timestamp = process_line(connection, line, last_timestamp)

            except MySQLError as exc:
                print(f"[ERROR] MySQL-Fehler: {exc}", file=sys.stderr, flush=True)
                print("[INFO] Versuche MySQL-Verbindung neu aufzubauen ...", file=sys.stderr, flush=True)

                try:
                    if connection is not None and connection.is_connected():
                        connection.close()
                except MySQLError:
                    pass

                time.sleep(5)
                connection = connect_mysql()

    except KeyboardInterrupt:
        print("", flush=True)
        print("Beendet durch Benutzer.", flush=True)

    finally:
        if connection is not None:
            try:
                if connection.is_connected():
                    connection.close()
                    print("MySQL-Verbindung geschlossen.", flush=True)
            except MySQLError:
                pass


if __name__ == "__main__":
    main()
