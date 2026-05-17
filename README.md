# RTL-SDR Weather Station Logger

This project receives weather data from a wireless weather station using `rtl_433`, processes the JSON data with Python, and stores it in a MySQL/MariaDB database.

The weather station identifies itself as:

```text
Fineoffset-WHx080
```

Example received frame:

```json
{
  "time": "2026-05-17 01:50:09",
  "model": "Fineoffset-WHx080",
  "subtype": 0,
  "id": 228,
  "battery_ok": 1,
  "temperature_C": 3.600,
  "humidity": 90,
  "wind_dir_deg": 0,
  "wind_avg_km_h": 0.000,
  "wind_max_km_h": 0.000,
  "rain_mm": 926.700,
  "mic": "CRC"
}
```

The following values are stored:

- Timestamp
- Station ID
- Battery status
- Temperature
- Humidity
- Wind direction
- Average wind speed
- Maximum wind speed
- Rain counter

---

## Requirements

Required packages:

```bash
rtl_433
python3
python3-venv
python3-pip
mysql-server or mariadb-server
apache2 or another web server with PHP
php-mysql
screen
git
```

Example for Ubuntu/Debian:

```bash
sudo apt update
sudo apt install rtl-433 python3 python3-venv python3-pip mariadb-server apache2 php php-mysql screen git
```

Depending on your distribution, the package may be called `rtl_433` instead of `rtl-433`.

---

## Clone the repository

```bash
git clone https://github.com/Foxconn11/rtlsdr_weatherstation.git
cd rtlsdr_weatherstation
```

---

## Database setup

The database structure is located in:

```text
mysql/wetter.sql
```

This file contains the structure for the database.

### Create database and user

Log in to MySQL/MariaDB:

```bash
sudo mysql
```

Create the database:

```sql
CREATE DATABASE wetter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Create the database user:

```sql
CREATE USER 'wetter'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
```

If the Python script accesses the database from another machine, use `%` or the specific IP address instead of `localhost`:

```sql
CREATE USER 'wetter'@'%' IDENTIFIED BY 'YOUR_PASSWORD';
```

Grant permissions:

```sql
GRANT ALL PRIVILEGES ON wetter.* TO 'wetter'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

For access from another machine:

```sql
GRANT ALL PRIVILEGES ON wetter.* TO 'wetter'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### Import database structure

From the repository directory:

```bash
mysql -u wetter -p wetter < mysql/wetter.sql
```

After that, the table `data` should exist.

---

## Web server setup

The files for the web server are located in:

```text
put_on_webserver
```

Copy these files to your web server directory, for example:

```bash
sudo cp -r put_on_webserver/* /var/www/html/
```

Or into a dedicated subfolder:

```bash
sudo mkdir -p /var/www/html/wetter
sudo cp -r put_on_webserver/* /var/www/html/wetter/
```

### Configure database connection

Inside the web server folder, there is an example file:

```text
connection.php.example
```

Copy or rename it to:

```text
connection.php
```

Example:

```bash
cd /var/www/html/wetter
sudo cp connection.php.example connection.php
```

Edit it:

```bash
sudo nano connection.php
```

Enter your database credentials:

```php
'host' => 'localhost',
'name' => 'wetter',
'user' => 'wetter',
'pass' => 'YOUR_PASSWORD',
```

If the database runs on another server, adjust `host` accordingly.

Example:

```php
'host' => '192.168.0.19',
'name' => 'wetter',
'user' => 'wetter',
'pass' => 'YOUR_PASSWORD',
```

After that, the web page can be opened in your browser, for example:

```text
http://SERVER-IP/wetter/
```

or the API:

```text
http://SERVER-IP/wetter/wetter_api.php
```

---

## Receiver script setup

The receiver script is located in:

```text
recieverscript
```

Note: If the folder is named this way in the repository, keep this spelling.

Go into the folder:

```bash
cd recieverscript
```

### Create settings file

The example file:

```text
settings.example.py
```

must be copied to:

```text
settings.py
```

Copy it:

```bash
cp settings.example.py settings.py
```

Edit it:

```bash
nano settings.py
```

Example:

```python
MYSQL_CONFIG = {
    "host": "192.168.0.19",
    "user": "wetter",
    "password": "YOUR_PASSWORD",
    "database": "wetter",
}

STATION_ID = 228
```

Important settings:

| Setting | Description |
|---|---|
| `host` | IP address or hostname of the MySQL/MariaDB server |
| `user` | MySQL user |
| `password` | MySQL password |
| `database` | Database name, usually `wetter` |
| `STATION_ID` | ID of your weather station |

### Find the station ID

You can find the station ID using `rtl_433`:

```bash
rtl_433 -F json
```

Or with the matching decoder:

```bash
rtl_433 -R 32 -F json
```

Look for an output like this:

```json
"id": 228
```

Enter this ID in `settings.py`:

```python
STATION_ID = 228
```

---

## Create Python venv

Inside the `recieverscript` folder, create a virtual Python environment:

```bash
python3 -m venv venv
```

Activate the venv:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Test it:

```bash
python -c "import mysql.connector; print('mysql connector ok')"
```

If everything is working, you should see:

```text
mysql connector ok
```

You can leave the venv afterwards:

```bash
deactivate
```

---

## Manual test

Inside the `recieverscript` folder:

```bash
source venv/bin/activate
rtl_433 -R 32 -F json | python -u weather_receiver.py
```

If you use an SDR stick with a specific EEPROM serial number:

```bash
rtl_433 -d :00000999 -R 32 -F json | python -u weather_receiver.py
```

If everything works, you should see output like this when a frame is received:

```text
New weather frame received
Temperature: 3.6 °C
Humidity: 90 %
Wind direction: 0 °
Wind speed: 0.0 km/h
Maximum wind speed: 0.0 km/h
Rain: 926.7 mm
Battery status: Full
Sender timestamp: 2026-05-17 01:50:09

[OK] Record inserted: 2026-05-17 01:50:09 | 3.6 °C | 90 % | rain counter 926.7 mm
```

Stop with:

```text
CTRL+C
```

---

## Running with crontab

The folder `recieverscript` contains the file:

```text
wettersdr.sh
```

This file starts `rtl_433` and pipes the JSON data to the Python script.

### Configure SDR stick

Inside `wettersdr.sh`, there is the `rtl_433` start command.

If you use an SDR stick with an EEPROM serial number:

```bash
rtl_433 -d :00000999 -R 32 -F json
```

Replace `00000999` with your own SDR serial number.

If you only have one SDR stick or do not want to use a serial number, remove the `-d` part:

```bash
rtl_433 -R 32 -F json
```

### Make the script executable

```bash
chmod +x wettersdr.sh
```

### Open crontab

```bash
crontab -e
```

Add this line:

```cron
@reboot screen -d -m /home/path/rtlsdr_weatherstation/recieverscript/wettersdr.sh &
```

Adjust the path to your own installation.

Example:

```cron
@reboot screen -d -m /home/USERNAME/rtlsdr_weatherstation/recieverscript/wettersdr.sh &
```

After a reboot, the script will run inside a `screen` session.

---

## Running as a systemd service

Alternatively, the script can be run as a systemd service.

The service file is located in:

```text
settings/weatherstation.service
```

Copy it to systemd:

```bash
sudo cp settings/weatherstation.service /etc/systemd/system/weatherstation.service
```

Edit it:

```bash
sudo nano /etc/systemd/system/weatherstation.service
```

### Adjust WorkingDirectory

Inside the service file, adjust the working directory:

```ini
WorkingDirectory=/home/path/rtlsdr_weatherstation/recieverscript
```

Example:

```ini
WorkingDirectory=/home/USERNAME/rtlsdr_weatherstation/recieverscript
```

### Configure SDR stick

The service file also contains the `rtl_433` start command.

If you use an SDR stick with a serial number:

```bash
rtl_433 -d :00000999 -R 32 -F json
```

Replace `00000999` with your own SDR serial number.

If you do not want to use an SDR ID, remove the `-d :00000999` part:

```bash
rtl_433 -R 32 -F json
```

### Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable weatherstation.service
sudo systemctl start weatherstation.service
```

Show service status:

```bash
sudo systemctl status weatherstation.service
```

Show live logs:

```bash
journalctl -u weatherstation.service -f
```

Restart the service:

```bash
sudo systemctl restart weatherstation.service
```

Stop the service:

```bash
sudo systemctl stop weatherstation.service
```

---

## Automatic restart notes

The systemd service should be configured to automatically restart on failure.

Recommended:

```ini
Restart=always
RestartSec=60
```

This makes systemd wait 60 seconds before restarting the service after a failure. It prevents the service from entering an aggressive restart loop.

---

## Git notes

Files containing real credentials should not be committed to the Git repository.

Recommended `.gitignore`:

```gitignore
settings.py
connection.php
venv/
.venv/
__pycache__/
*.pyc
```

Use example files instead:

```text
settings.example.py
connection.php.example
```

---

## Common issues

### `ModuleNotFoundError: No module named 'mysql'`

The Python dependencies were not installed inside the venv.

Solution:

```bash
cd recieverscript
source venv/bin/activate
pip install -r requirements.txt
```

### No data is being stored

Check:

```bash
rtl_433 -R 32 -F json
```

If no JSON data appears, `rtl_433` is not receiving the weather station.

If JSON data appears but nothing is stored:

- Check `STATION_ID` in `settings.py`
- Check database credentials
- Check script or service logs

### MySQL is not immediately available after reboot

If the script runs as a systemd service, it should restart automatically with:

```ini
Restart=always
RestartSec=60
```

The Python script should also handle MySQL errors and try to reconnect.

---

## Complete example setup

Clone repository:

```bash
git clone https://github.com/Foxconn11/rtlsdr_weatherstation.git
cd rtlsdr_weatherstation
```

Create database:

```bash
sudo mysql
```

Inside MySQL:

```sql
CREATE DATABASE wetter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wetter'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON wetter.* TO 'wetter'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Import database structure:

```bash
mysql -u wetter -p wetter < mysql/wetter.sql
```

Set up receiver:

```bash
cd recieverscript
cp settings.example.py settings.py
nano settings.py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Test:

```bash
rtl_433 -R 32 -F json | python -u weather_receiver.py
```

Install service:

```bash
sudo cp ../settings/weatherstation.service /etc/systemd/system/weatherstation.service
sudo nano /etc/systemd/system/weatherstation.service
sudo systemctl daemon-reload
sudo systemctl enable weatherstation.service
sudo systemctl start weatherstation.service
```

Logs:

```bash
journalctl -u weatherstation.service -f
```
