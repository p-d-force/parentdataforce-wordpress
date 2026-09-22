<?php
/**
 * One-shot server helper: serialized-aware URL search-replace across posts
 * and postmeta (skips guid by design).
 *
 * ?key=SECRET  -> replace https://www.parentdataforce.com/news/ with
 *                 https://www.parentdataforce.com/ in posts.post_content,
 *                 posts.post_excerpt, posts.post_title, and postmeta.
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
$from = 'https://www.parentdataforce.com/news/';
$to = 'https://www.parentdataforce.com/';
$changed = [];

foreach (['post_content', 'post_excerpt', 'post_title'] as $col) {
    $rows = $wpdb->get_results("SELECT ID, `$col` AS val FROM {$wpdb->posts} WHERE `$col` LIKE %s", ARRAY_A);
    $rows = $wpdb->get_results($wpdb->prepare("SELECT ID, `$col` AS val FROM {$wpdb->posts} WHERE `$col` LIKE %s", '%' . $wpdb->esc_like($from) . '%'), ARRAY_A);
    foreach ($rows as $row) {
        $new = str_replace($from, $to, $row['val']);
        $wpdb->update($wpdb->posts, [$col => $new], ['ID' => $row['ID']]);
        $changed['posts.' . $col][] = (int) $row['ID'];
    }
}

$metas = $wpdb->get_results($wpdb->prepare("SELECT meta_id, meta_key, meta_value FROM {$wpdb->postmeta} WHERE meta_value LIKE %s", '%' . $wpdb->esc_like($from) . '%'), ARRAY_A);
foreach ($metas as $m) {
    $val = $m['meta_value'];
    if (is_serialized($val)) {
        $un = @unserialize($val);
        if ($un !== false || $val === 'b:0;') {
            $walk = function (&$item) use (&$walk, $from, $to) {
                if (is_string($item)) { $item = str_replace($from, $to, $item); }
                elseif (is_array($item)) { array_walk_recursive($item, function (&$v) use (&$walk, $from, $to) { $walk($v); }); }
            };
            $walk($un);
            $new = serialize($un);
        } else {
            $new = str_replace($from, $to, $val);
        }
        $wpdb->update($wpdb->postmeta, ['meta_value' => $new], ['meta_id' => $m['meta_id']]);
        $changed['postmeta.' . $m['meta_key']][] = (int) $m['post_id'];
    } else {
        $new = str_replace($from, $to, $val);
        $wpdb->update($wpdb->postmeta, ['meta_value' => $new], ['meta_id' => $m['meta_id']]);
        $changed['postmeta.' . $m['meta_key']][] = (int) $m['post_id'];
    }
}

echo json_encode(['from' => $from, 'changed' => $changed], JSON_PRETTY_PRINT);
