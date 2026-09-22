<?php
/**
 * Temporary migration diagnostic mu-plugin. Remove after the root cutover
 * settles.
 */
add_action('parse_request', function () { @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', date('c') . ' PARSE_REQUEST' . PHP_EOL, FILE_APPEND); });
add_action('wp', function () { @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', date('c') . ' WP_LOADED' . PHP_EOL, FILE_APPEND); }, 1);
add_action('template_redirect', function () { @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', date('c') . ' TEMPLATE_REDIRECT fired' . PHP_EOL, FILE_APPEND); }, 1);
add_filter('redirect_canonical', function ($url, $requested) {
    @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', date('c') . ' REDIRECT_CANONICAL=' . var_export($url, true) . PHP_EOL, FILE_APPEND);
    return $url;
}, 10, 2);
add_filter('template_include', function ($template) {
    @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', date('c') . ' TEMPLATE=' . var_export($template, true) . PHP_EOL, FILE_APPEND);
    return $template;
}, PHP_INT_MAX);
add_action('shutdown', function () {
    $e = error_get_last();
    $line = date('c') . ' URI=' . ($_SERVER['REQUEST_URI'] ?? '?')
        . ' ob_level=' . ob_get_level()
        . ' out_len=' . (function_exists('ob_get_length') && ob_get_length() !== false ? ob_get_length() : -1);
    if ($e && in_array($e['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR], true)) {
        $line .= ' FATAL=' . $e['message'] . ' @' . $e['file'] . ':' . $e['line'];
    }
    @file_put_contents(WP_CONTENT_DIR . '/pdf-debug.log', $line . PHP_EOL, FILE_APPEND);
});
