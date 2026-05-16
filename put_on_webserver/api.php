<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');

$config = require __DIR__ . '/connection.php';

function getPdo(array $config): PDO
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
    $stmt = $pdo->query("
        SELECT `rain_mm`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
        ORDER BY `timestamp` ASC
        LIMIT 1
    ");

    $old = $stmt->fetch();

    if (!$old || $old['rain_mm'] === null) {
        return null;
    }

    $difference = $currentRain - (float)$old['rain_mm'];

    /*
     * Falls der Regenzähler resettet oder springt:
     * keine negativen Regenwerte ausgeben.
     */
    if ($difference < 0) {
        return 0.0;
    }

    return round($difference, 4);
}

function getAverageTemperature(PDO $pdo, string $interval): ?float
{
    $stmt = $pdo->query("
        SELECT AVG(`temperature`) AS `avg_temperature`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
    ");

    $row = $stmt->fetch();

    if (!$row || $row['avg_temperature'] === null) {
        return null;
    }

    return round((float)$row['avg_temperature'], 2);
}

function getTemperatureStat(PDO $pdo, string $interval, string $order): ?array
{
    $order = strtoupper($order) === 'ASC' ? 'ASC' : 'DESC';

    $stmt = $pdo->query("
        SELECT `temperature`, `timestamp`
        FROM `data`
        WHERE `timestamp` >= NOW() - INTERVAL {$interval}
        ORDER BY `temperature` {$order}
        LIMIT 1
    ");

    $row = $stmt->fetch();

    return $row ?: null;
}

try {
    $pdo = getPdo($config);

    /*
     * Aktuellster Frame
     */
    $current = getCurrent($pdo);

    if (!$current) {
        http_response_code(404);

        echo json_encode([
            'success' => false,
            'error' => 'no_data',
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

        exit;
    }

    $currentRain = isset($current['rain_mm']) ? (float)$current['rain_mm'] : 0.0;

    /*
     * Regenwerte
     */
    $rainLastHour = getRainDifference($pdo, $currentRain, '1 HOUR');
    $rainLast24h = getRainDifference($pdo, $currentRain, '1 DAY');

    /*
     * Durchschnittstemperatur letzte 12 Stunden
     */
    $avgTemp12h = getAverageTemperature($pdo, '12 HOUR');

    /*
     * Temperatur High/Low
     */
    $tempHigh24h = getTemperatureStat($pdo, '1 DAY', 'DESC');
    $tempLow24h = getTemperatureStat($pdo, '1 DAY', 'ASC');

    $tempHigh7d = getTemperatureStat($pdo, '1 WEEK', 'DESC');
    $tempLow7d = getTemperatureStat($pdo, '1 WEEK', 'ASC');

    /*
     * JSON-Ausgabe
     */
    $response = [
        'success' => true,

        'current' => [
            'id' => isset($current['ID']) ? (int)$current['ID'] : null,
            'timestamp' => $current['timestamp'] ?? null,

            'temperature' => isset($current['temperature']) ? (float)$current['temperature'] : null,
            'humidity' => isset($current['humidity']) ? (float)$current['humidity'] : null,

            'winddirection' => isset($current['winddirection']) ? (int)$current['winddirection'] : null,
            'wind_avg' => isset($current['wind_avg']) ? (float)$current['wind_avg'] : null,
            'wind_max' => isset($current['wind_max']) ? (float)$current['wind_max'] : null,

            'rain_mm' => isset($current['rain_mm']) ? (float)$current['rain_mm'] : null,
            'battery' => isset($current['battery']) ? (int)$current['battery'] : null,
        ],

        'rain' => [
            'last_1h' => $rainLastHour,
            'last_24h' => $rainLast24h,
        ],

        'temperature_stats' => [
            'avg_12h' => $avgTemp12h,

            'high_24h' => [
                'value' => isset($tempHigh24h['temperature']) ? (float)$tempHigh24h['temperature'] : null,
                'timestamp' => $tempHigh24h['timestamp'] ?? null,
            ],

            'low_24h' => [
                'value' => isset($tempLow24h['temperature']) ? (float)$tempLow24h['temperature'] : null,
                'timestamp' => $tempLow24h['timestamp'] ?? null,
            ],

            'high_7d' => [
                'value' => isset($tempHigh7d['temperature']) ? (float)$tempHigh7d['temperature'] : null,
                'timestamp' => $tempHigh7d['timestamp'] ?? null,
            ],

            'low_7d' => [
                'value' => isset($tempLow7d['temperature']) ? (float)$tempLow7d['temperature'] : null,
                'timestamp' => $tempLow7d['timestamp'] ?? null,
            ],
        ],
    ];

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    http_response_code(500);

    echo json_encode([
        'success' => false,
        'error' => 'server_error',
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
