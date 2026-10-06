<?php
/**
 * One-shot server helper: delete specific PENDING queue-vote posts by id
 * (post type pdforce_queue_note, title "vote|District", meta pdforce_ingested
 * falsy). Used to undo a local vote-button click test so no test vote ships.
 *
 *   ?key=SECRET             -> dry run: report each id, its district, pending
 *   &ids=394,395            -> force-delete exactly those ids, and only if
 *                              each is a pending vote post
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

$ids = isset($_GET['ids']) ? $_GET['ids'] : '';
$ids = array_values(array_filter(array_map('intval', explode(',', $ids))));

$rows = array();
foreach ($ids as $id) {
    $p = get_post($id);
    if (!$p || $p->post_type !== 'pdforce_queue_note') {
        $rows[] = array('id' => $id, 'ok' => false, 'why' => 'not a queue-note post');
        continue;
    }
    $meta = get_post_meta($id, 'pdforce_ingested', true);
    $raw = (string) $p->post_content;
    $is_vote = (0 === strpos($raw, 'vote|')) || (0 === strpos($raw, 'vote-ga|'));
    $pending = $is_vote && empty($meta);
    $row = array(
        'id' => $id,
        'title' => $p->post_title,
        'content' => $raw,
        'date' => $p->post_date,
        'ingested' => (string) $meta,
        'pending' => $pending,
    );
    if (!empty($_GET['do']) && $pending) {
        wp_delete_post($id, true);
        $row['deleted'] = true;
    } else {
        $row['deleted'] = false;
    }
    $rows[] = $row;
}

echo json_encode(array('rows' => $rows), JSON_PRETTY_PRINT);
