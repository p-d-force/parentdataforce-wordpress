<?php
/**
 * One-shot server helper: flip the WP home URL to the site root and flush.
 *
 * Upload next to wp-load.php, invoke once with the secret, then DELETE.
 *
 * ?key=SECRET&action=verify  -> report current home/siteurl + sample permalink
 * ?key=SECRET&action=cut     -> set home=https://www.parentdataforce.com/, flush
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

$action = isset($_GET['action']) ? preg_replace('/[^a-z]/', '', $_GET['action']) : 'verify';
$out = [
    'siteurl_before' => get_option('siteurl'),
    'home_before' => get_option('home'),
];

if ($action === 'cut') {
    update_option('home', 'https://www.parentdataforce.com/');
    global $wp_rewrite;
    $wp_rewrite->init();
    $wp_rewrite->flush_rules(true);
}

$out['action'] = $action;
$out['siteurl_after'] = get_option('siteurl');
$out['home_after'] = get_option('home');
$out['permalink_structure'] = get_option('permalink_structure');
$out['sample_page_link'] = get_permalink(57);
$out['sample_post_link'] = get_permalink(49);

echo json_encode($out, JSON_PRETTY_PRINT);
