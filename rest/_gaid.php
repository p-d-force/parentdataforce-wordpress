<?php
/**
 * One-shot server helper: read Google Site Kit analytics settings.
 *
 * Upload to the WordPress root (next to wp-load.php), invoke once over HTTP
 * with the secret key, then DELETE it from the server.
 *
 * Read-only: dumps the Site Kit analytics settings option so the live
 * measurement ID can be recovered without wp-admin access.
 *
 * ?key=SECRET   -> JSON of googlesitekit_analytics_settings (+ module active state)
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

$out = [
    'analytics_settings' => get_option('googlesitekit_analytics_settings', null),
    'adsense_settings' => get_option('googlesitekit_adsense_settings', null),
    'active_plugins' => array_values(array_map(function ($f) {
        return basename(dirname($f)) . '/' . basename($f);
    }, (array) glob(WP_PLUGIN_DIR . '/*/*.php'))),
];

echo json_encode($out, JSON_PRETTY_PRINT);
