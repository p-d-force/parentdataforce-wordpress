<?php
require_once __DIR__.'/wp-load.php';
header('Content-Type: application/json');
global $wpdb;
$uid = 1;

// Read new password from environment variable for security
$new_pw = getenv('WP_NEW_PW');
if (!$new_pw) {
    http_response_code(400);
    echo json_encode(['error' => 'WP_NEW_PW environment variable required']);
    exit;
}

$ur = wp_update_user(['ID' => $uid, 'user_pass' => $new_pw]);
$out['update'] = is_wp_error($ur) ? $ur->get_error_code() : 'ok';

// Verify against the raw master hash (bypasses any object-cache lag)
$row = $wpdb->get_row($wpdb->prepare("SELECT user_pass FROM {$wpdb->users} WHERE ID=%d", $uid), ARRAY_A);
$out['raw_pass_len'] = $row ? strlen($row['user_pass']) : 0;
$out['valid'] = ($row && $row['user_pass']) ? wp_check_password($new_pw, $row['user_pass']) : false;

wp_cache_delete($uid, 'users');
wp_cache_delete($uid, 'user_meta');

echo json_encode($out, JSON_PRETTY_PRINT);
