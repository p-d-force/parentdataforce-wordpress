<?php
/**
 * Title: 404 — signal lost
 * Slug: pdforce/hidden-404
 * Inserter: no
 * Description: Full-width ASCII fault scene with a "signal lost" message.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

?>
<!-- wp:group {"tagName":"div","align":"full","className":"pdf-404","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull pdf-404">
	<!-- wp:html -->
	<canvas class="pdf-ascii" data-scene="hero" data-cell="17" role="img" aria-label="Animated artwork: a fault line in a dark field"></canvas>
	<!-- /wp:html -->

	<!-- wp:group {"className":"pdf-404-body","layout":{"type":"constrained"}} -->
	<div class="wp-block-group pdf-404-body">
		<!-- wp:paragraph {"className":"pdf-kicker"} -->
		<p class="pdf-kicker"><?php esc_html_e( '404 — Signal Lost', 'pdforce' ); ?></p>
		<!-- /wp:paragraph -->

		<!-- wp:heading {"level":1} -->
		<h1 class="wp-block-heading"><?php esc_html_e( 'This record isn’t in the file.', 'pdforce' ); ?></h1>
		<!-- /wp:heading -->

		<!-- wp:paragraph -->
		<p><?php esc_html_e( 'The page you’re looking for doesn’t exist or was moved. Try a search, or head back to the record index.', 'pdforce' ); ?></p>
		<!-- /wp:paragraph -->

		<!-- wp:pattern {"slug":"pdforce/hidden-search"} /-->
	</div>
	<!-- /wp:group -->
</div>
<!-- /wp:group -->
