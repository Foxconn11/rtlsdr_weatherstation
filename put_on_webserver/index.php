<?php
declare(strict_types=1);

$config = require __DIR__ . '/connection.php';

function db(array $config): PDO
{
    $db = $config['db'];

    return new PDO(
        "mysql:host={$db['host']};dbname={$db['name']};charset={$db['charset']}",
        $db['user'],
        $db['pass'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
}

function formatNumber($value, int $decimals = 1): string
{
    if ($value === null || $value === '') {
        return '—';
    }

    return number_format((float)$value, $decimals, ',', '.');
}

function formatDateTime($value): string
{
    if (!$value) {
        return '—';
    }

    return date('d.m.Y H:i:s', strtotime((string)$value));
}

function windDirectionText($degrees): string
{
    if ($degrees === null || $degrees === '') {
        return 'Unbekannt';
    }

    $deg = (float)$degrees;

    if ($deg >= 337.5 || $deg < 22.5) {
        return 'Norden';
    }
    if ($deg < 67.5) {
        return 'Nord-Ost';
    }
    if ($deg < 112.5) {
        return 'Osten';
    }
    if ($deg < 157.5) {
        return 'Süd-Ost';
    }
    if ($deg < 202.5) {
        return 'Süden';
    }
    if ($deg < 247.5) {
        return 'Süd-West';
    }
    if ($deg < 292.5) {
        return 'Westen';
    }
    if ($deg < 337.5) {
        return 'Nord-West';
    }

    return 'Unbekannt';
}

function batteryText($battery): string
{
    return ((string)$battery === '0') ? 'Leer' : 'Voll';
}

function getCurrent(PDO $pdo): ?array
{
    $stmt = $pdo->query("
        SELECT *
        FROM `data`
        ORDER BY `ID` DESC
        LIMIT 1
    ");

    $row = $stmt->fetch();

    return $row ?: null;
}

function getRainDifference(PDO $pdo, float $currentRain, string $interval): ?float
{
    $stmt = $pdo->prepare("
        SELECT `rain_mm`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
        ORDER BY `timestamp` ASC
        LIMIT 1
    ");

    $stmt->execute();
    $old = $stmt->fetch();

    if (!$old || $old['rain_mm'] === null) {
        return null;
    }

    $difference = $currentRain - (float)$old['rain_mm'];

    /*
     * Falls der Regenzähler resettet oder springt:
     * Negative Werte nicht anzeigen.
     */
    if ($difference < 0) {
        return 0.0;
    }

    return round($difference, 2);
}

function getTemperatureStat(PDO $pdo, string $interval, string $order): ?array
{
    $order = strtoupper($order) === 'ASC' ? 'ASC' : 'DESC';

    $stmt = $pdo->prepare("
        SELECT `temperature`, `timestamp`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
        ORDER BY `temperature` {$order}
        LIMIT 1
    ");

    $stmt->execute();
    $row = $stmt->fetch();

    return $row ?: null;
}

function getAverageTemperature(PDO $pdo, string $interval): ?float
{
    $stmt = $pdo->prepare("
        SELECT AVG(`temperature`) AS `avg_temperature`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
    ");

    $stmt->execute();
    $row = $stmt->fetch();

    if (!$row || $row['avg_temperature'] === null) {
        return null;
    }

    return round((float)$row['avg_temperature'], 2);
}

try {
    $pdo = db($config);

    $current = getCurrent($pdo);

    if (!$current) {
        throw new RuntimeException('Keine Wetterdaten vorhanden.');
    }

    $currentRain = isset($current['rain_mm']) ? (float)$current['rain_mm'] : 0.0;

    $rain1h = getRainDifference($pdo, $currentRain, '1 HOUR');
    $rain24h = getRainDifference($pdo, $currentRain, '1 DAY');

    $tempAvg12h = getAverageTemperature($pdo, '12 HOUR');

    $tempHigh24h = getTemperatureStat($pdo, '1 DAY', 'DESC');
    $tempLow24h = getTemperatureStat($pdo, '1 DAY', 'ASC');

    $tempHigh7d = getTemperatureStat($pdo, '1 WEEK', 'DESC');
    $tempLow7d = getTemperatureStat($pdo, '1 WEEK', 'ASC');

} catch (Throwable $e) {
    http_response_code(500);
    $error = $e->getMessage();
}

?>
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="60">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Auto-RX Wetterstation</title>

    <style>
        :root {
            --bg: #101214;
            --card: #1a1d21;
            --card-2: #22262b;
            --text: #f4f4f5;
            --muted: #a1a1aa;
            --accent: #4da3ff;
            --good: #58d68d;
            --warn: #f5b041;
            --border: #30343a;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, Helvetica, sans-serif;
            background: var(--bg);
            color: var(--text);
        }

        .page {
            width: min(1100px, 100%);
            margin: 0 auto;
            padding: 24px;
        }

        .header {
            margin-bottom: 24px;
            padding: 24px;
            background: linear-gradient(135deg, #1f2937, #111827);
            border: 1px solid var(--border);
            border-radius: 22px;
        }

        .header h1 {
            margin: 0;
            font-size: clamp(28px, 5vw, 46px);
            line-height: 1.1;
        }

        .header p {
            margin: 10px 0 0;
            color: var(--muted);
            font-size: 16px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }

        .card {
            padding: 20px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
        }

        .card.wide {
            grid-column: 1 / -1;
        }

        .label {
            margin-bottom: 8px;
            color: var(--muted);
            font-size: 14px;
        }

        .value {
            font-size: 30px;
            font-weight: 700;
            line-height: 1.2;
        }

        .unit {
            font-size: 18px;
            color: var(--muted);
        }

        .small {
            margin-top: 8px;
            color: var(--muted);
            font-size: 14px;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table tr {
            border-bottom: 1px solid var(--border);
        }

        .table tr:last-child {
            border-bottom: 0;
        }

        .table td {
            padding: 12px 4px;
        }

        .table td:last-child {
            text-align: right;
            font-weight: 700;
        }

        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: var(--card-2);
            color: var(--text);
            font-size: 14px;
        }

        .badge.good {
            background: rgba(88, 214, 141, 0.15);
            color: var(--good);
        }

        .badge.warn {
            background: rgba(245, 176, 65, 0.15);
            color: var(--warn);
        }

        .error {
            padding: 20px;
            background: #3b1f1f;
            border: 1px solid #7f1d1d;
            border-radius: 18px;
            color: #fecaca;
        }

        @media (max-width: 600px) {
            .page {
                padding: 14px;
            }

            .value {
                font-size: 26px;
            }
        }
    </style>
</head>
<body>
<div class="page">

    <div class="header">
        <h1>Auto-RX Wetterstation</h1>
        <p>Lokale SDR-Wetterdaten aus der MySQL-Datenbank</p>
    </div>

    <?php if (isset($error)): ?>
        <div class="error">
            <strong>Fehler:</strong> <?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?>
        </div>
    <?php else: ?>

        <div class="grid">
            <div class="card">
                <div class="label">Temperatur</div>
                <div class="value">
                    <?= formatNumber($current['temperature'], 1) ?>
                    <span class="unit">°C</span>
                </div>
                <div class="small">
                    Ø 12h: <?= formatNumber($tempAvg12h, 2) ?> °C
                </div>
            </div>

            <div class="card">
                <div class="label">Luftfeuchtigkeit</div>
                <div class="value">
                    <?= formatNumber($current['humidity'], 0) ?>
                    <span class="unit">%</span>
                </div>
            </div>

            <div class="card">
                <div class="label">Wind</div>
                <div class="value">
                    <?= formatNumber($current['wind_avg'], 2) ?>
                    <span class="unit">km/h</span>
                </div>
                <div class="small">
                    Max: <?= formatNumber($current['wind_max'], 2) ?> km/h
                </div>
            </div>

            <div class="card">
                <div class="label">Windrichtung</div>
                <div class="value">
                    <?= htmlspecialchars(windDirectionText($current['winddirection']), ENT_QUOTES, 'UTF-8') ?>
                </div>
                <div class="small">
                    <?= formatNumber($current['winddirection'], 0) ?>°
                </div>
            </div>

            <div class="card">
                <div class="label">Regen letzte 1h</div>
                <div class="value">
                    <?= formatNumber($rain1h, 2) ?>
                    <span class="unit">mm</span>
                </div>
                <div class="small">berechnet aus Regenzähler-Differenz</div>
            </div>

            <div class="card">
                <div class="label">Regen letzte 24h</div>
                <div class="value">
                    <?= formatNumber($rain24h, 2) ?>
                    <span class="unit">mm</span>
                </div>
                <div class="small">berechnet aus Regenzähler-Differenz</div>
            </div>

            <div class="card">
                <div class="label">Regen Gesamt</div>
                <div class="value">
                    <?= formatNumber($current['rain_mm'], 1) ?>
                    <span class="unit">mm</span>
                </div>
                <div class="small">Rohwert aus der Wetterstation</div>
            </div>

            <div class="card">
                <div class="label">Batterie</div>
                <div class="value">
                    <span class="badge <?= ((string)$current['battery'] === '0') ? 'warn' : 'good' ?>">
                        <?= batteryText($current['battery']) ?>
                    </span>
                </div>
                <div class="small">Rohwert: <?= htmlspecialchars((string)$current['battery'], ENT_QUOTES, 'UTF-8') ?></div>
            </div>

            <div class="card wide">
                <table class="table">
                    <tr>
                        <td>Letzter Frame</td>
                        <td><?= formatDateTime($current['timestamp']) ?></td>
                    </tr>
                    <tr>
                        <td>Temperatur High 24h</td>
                        <td>
                            <?= $tempHigh24h ? formatNumber($tempHigh24h['temperature'], 1) . ' °C · ' . formatDateTime($tempHigh24h['timestamp']) : '—' ?>
                        </td>
                    </tr>
                    <tr>
                        <td>Temperatur Low 24h</td>
                        <td>
                            <?= $tempLow24h ? formatNumber($tempLow24h['temperature'], 1) . ' °C · ' . formatDateTime($tempLow24h['timestamp']) : '—' ?>
                        </td>
                    </tr>
                    <tr>
                        <td>Temperatur High 7 Tage</td>
                        <td>
                            <?= $tempHigh7d ? formatNumber($tempHigh7d['temperature'], 1) . ' °C · ' . formatDateTime($tempHigh7d['timestamp']) : '—' ?>
                        </td>
                    </tr>
                    <tr>
                        <td>Temperatur Low 7 Tage</td>
                        <td>
                            <?= $tempLow7d ? formatNumber($tempLow7d['temperature'], 1) . ' °C · ' . formatDateTime($tempLow7d['timestamp']) : '—' ?>
                        </td>
                    </tr>
                </table>
            </div>
        </div>

    <?php endif; ?>

</div>
</body>
</html>
