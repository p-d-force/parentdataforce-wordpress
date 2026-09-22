<?php
/**
 * WordPress front controller — the install lives at /news/, URLs serve
 * from the site root. Replaces the legacy static homepage on 2026-09-22
 * (the old static home is preserved as index-static-home.php).
 */

/**
 * Tells WordPress to load the WordPress theme and output it.
 *
 * @var bool
 */
define( 'WP_USE_THEMES', true );

/** Loads the WordPress Environment and Template */
require __DIR__ . '/news/wp-blog-header.php';
