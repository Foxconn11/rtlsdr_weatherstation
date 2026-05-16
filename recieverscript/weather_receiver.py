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
    """Stellt die Verbindung zur MySQL-Datenbank her."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def parse_timestamp(timestamp: str) -> float:
    """Wandelt den Zeitstempel der Wetterstation in Unix-Zeit um."""
    return time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))


def get_required(data: Dict[str, Any], key: str) -> Any:
    """Liest ein Pflichtfeld aus dem JSON und wirft einen klaren Fehler, wenn es fehlt."""
    if key not in data:
        raise KeyError(f"Pflichtfeld fehlt: {key}")
    return data[key]


def is_target_station(data: Dict[str, Any]) -> bool:
    """Prüft, ob der empfangene Frame von der gewünschten Wetterstation kommt."""
    return int(get_required(data, "id")) == STATION_ID


def print_weather_data(data: Dict[str, Any]) -> None:
    """Gibt die empfangenen Wetterdaten lesbar auf der Konsole aus."""
    battery_ok = int(get_required(data, "battery_ok"))

    print("Neuer Wetter-Frame empfangen")
    print(f"Temperatur: {data['temperature_C']} °C")
    print(f"Luftfeuchtigkeit: {data['humidity']} %")
    print(f"Windrichtung: {data['wind_dir_deg']} °")
    print(f"Windgeschwindigkeit: {data['wind_avg_km_h']} km/h")
    print(f"Maximale Windgeschwindigkeit: {data['wind_max_km_h']} km/h")
    print(f"Niederschlag: {data['rain_mm']} mm")
    print(f"Batteriestand: {'Voll' if battery_ok == 1 else 'Leer'}")
    print(f"Zeitstempel des Senders: {data['time']}")
    print()


def insert_weather_data(connection, data: Dict[str, Any]) -> None:
    """Schreibt einen Wetterdatensatz in die MySQL-Datenbank."""
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
        print(f"{cursor.rowcount} Datensatz eingefügt.")
    finally:
        cursor.close()


def ensure_connection(connection):
    """Prüft die MySQL-Verbindung und verbindet bei Bedarf neu."""
    try:
        if connection is None or not connection.is_connected():
            return connect_mysql()
        return connection
    except MySQLError:
        return connect_mysql()


def process_line(connection, line: str, last_timestamp: Optional[float]) -> Optional[float]:
    """Verarbeitet eine einzelne JSON-Zeile von rtl_433."""
    line = line.strip()

    if not line:
        return last_timestamp

    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        print(f"Ungültiges JSON verworfen: {exc}", file=sys.stderr)
        return last_timestamp

    try:
        if not is_target_station(data):
            return last_timestamp

        timestamp_text = get_required(data, "time")
        timestamp = parse_timestamp(timestamp_text)

        if timestamp == last_timestamp:
            print("Datensatz bereits empfangen. Verwerfe Duplikat.")
            print()
            return last_timestamp

        print_weather_data(data)
        insert_weather_data(connection, data)

        return timestamp

    except KeyError as exc:
        print(f"Frame unvollständig, verworfen: {exc}", file=sys.stderr)
        return last_timestamp

    except ValueError as exc:
        print(f"Frame enthält ungültige Werte, verworfen: {exc}", file=sys.stderr)
        return last_timestamp

    except MySQLError as exc:
        print(f"MySQL-Fehler: {exc}", file=sys.stderr)
        raise


def main() -> None:
    print("Auto-RX Wetterstation Receiver gestartet.")
    print(f"Filtere auf Station-ID: {STATION_ID}")
    print("Warte auf rtl_433 JSON-Daten über STDIN ...")
    print()

    connection = None
    last_timestamp: Optional[float] = None

    try:
        connection = connect_mysql()

        for line in sys.stdin:
            try:
                connection = ensure_connection(connection)
                last_timestamp = process_line(connection, line, last_timestamp)
            except MySQLError:
                print("Versuche MySQL-Verbindung neu aufzubauen ...", file=sys.stderr)

                try:
                    if connection is not None and connection.is_connected():
                        connection.close()
                except MySQLError:
                    pass

                connection = connect_mysql()

    except KeyboardInterrupt:
        print()
        print("Beendet durch Benutzer.")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("MySQL-Verbindung geschlossen.")


if __name__ == "__main__":
    main()
