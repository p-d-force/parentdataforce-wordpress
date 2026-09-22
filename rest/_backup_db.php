<?php
/**
 * One-shot server helper: full database backup before the root migration.
 *
 * Upload next to wp-load.php, invoke once with the secret key, then DELETE.
 * Dumps every table (schema + rows) into /public_html/backups/ and returns a
 * JSON manifest. Read-only for the database.
 */
require_once __DIR__ . '/wp-load.php';

header('Content-Type: application/json');

$secret = '__SECRET__';
$key = isset($_GET['key']) ? $_GET['key'] : '';
if (!hash_equals($secret, $key)) {
    http_response_code(403);
    echo json_encode(['error' => 'forbidden']);
    exit;
}

global $wpdb;
$tables = $wpdb->get_col('SHOW TABLES');
$dir = dirname(ABSPATH) . '/backups';
if (!is_dir($file = $dir)) { @mkdir($dir, 0755, true); }
$file = $dir . '/db-pre-root-migration-' . date('Y-m-d-His') . '.sql';
$fh = fopen($file, 'w');
fwrite($fh, "-- Parent Data Force WP backup before root migration\n");
fwrite($fh, "-- generated " . date('c') . "\n");
fwrite($fh, "SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n");
$info = [];
foreach ($tables as $t) {
    $create = $wpdb->get_row("SHOW CREATE TABLE `$t`", ARRAY_N);
    fwrite($fh, "\nDROP TABLE IF EXISTS `$t`;\n" . $create[1] . ";\n");
    $rows = $wpdb->get_results("SELECT * FROM `$t`", ARRAY_A);
    $info[$t] = count($rows);
    foreach ($rows as $row) {
        $vals = [];
        foreach ($row as $col => $val) {
            if (is_null($val)) { $v = 'NULL'; }
            else { $v = "'" . esc_sql($val) . "'"; }
            $cols[] = "`$col`";
            $vals[] = $v;
        }
        fwrite($fh, "INSERT INTO `$t` (" . implode(',', $cols) . ") VALUES (" . implode(',', $vals) . ");\n");
        unset($cols, $vals);
    }
}
fwrite($fh, "SET FOREIGN_KEY_CHECKS=1;\n");
fclose($fh);

clearstatcache();
echo json_encode([
    'file' => basename($file),
    'bytes' => filesize($file),
    'tables' => count($tables),
    'rows' => $info,
], JSON_PRETTY_PRINT);
