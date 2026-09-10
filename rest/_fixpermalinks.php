<?php
/**
 * One-shot server helper: fix permalinks and (optionally) switch theme.
 *
 * Upload to the WordPress root (next to wp-load.php), invoke once over HTTP
 * with the secret key, then DELETE it from the server. tools/deploy_theme.py
 * does exactly that: it replaces __SECRET__ with a random token at upload
 * time, calls this script, verifies, and removes it.
 *
 * Actions:
 *   ?key=SECRET                -> set permalink_structure=/%postname%/, flush rules
 *   &switch=pdforce            -> also switch_theme('pdforce')
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

$out = [];

if (!empty($_GET['switch'])) {
    $stylesheet = sanitize_key($_GET['switch']);
    switch_theme($stylesheet);
    $out['switch_theme'] = get_stylesheet();
}

update_option('permalink_structure', '/%postname%/');
global $wp_rewrite;
$wp_rewrite->init();
$wp_rewrite->flush_rules();

$out['permalink_structure'] = get_option('permalink_structure');
$out['sample_permalink'] = get_permalink(1);
$out['active_theme'] = wp_get_theme()->get_stylesheet();
$out['theme_name'] = wp_get_theme()->get('Name');

echo json_encode($out, JSON_PRETTY_PRINT);
