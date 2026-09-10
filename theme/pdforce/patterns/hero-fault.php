<?php
/**
 * Title: Fault-line hero
 * Slug: pdforce/hero-fault
 * Categories: pdforce_page, featured
 * Description: Full-width hero. The animated fault-line logo is the centerpiece
 *              while public records spill out of the crack over a quiet ASCII
 *              data field and starfield.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

$pdf_logo = get_template_directory_uri() . '/assets/images/logo-animated.svg';
?>
<!-- wp:group {"tagName":"section","align":"full","className":"pdf-hero","layout":{"type":"default"}} -->
<section class="wp-block-group alignfull pdf-hero">
	<!-- wp:html -->
	<canvas class="pdf-ascii" data-scene="hero" data-cell="15" data-emit-from=".pdf-hero-logo" role="img" aria-label="Animated artwork: the Parent Data Force fault-line logo with public records spilling out of it"></canvas>
	<!-- /wp:html -->

	<!-- wp:group {"className":"pdf-hero-inner","layout":{"type":"constrained"}} -->
	<div class="wp-block-group pdf-hero-inner">
		<!-- wp:group {"className":"pdf-hero-text","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-hero-text">
			<!-- wp:paragraph {"className":"pdf-kicker"} -->
			<p class="pdf-kicker"><?php esc_html_e( 'Parent Data Force — News & Records', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->

			<!-- wp:heading {"level":1,"className":"pdf-hero-title"} -->
			<h1 class="wp-block-heading pdf-hero-title"><?php esc_html_e( 'The record, cracked open.', 'pdforce' ); ?></h1>
			<!-- /wp:heading -->

			<!-- wp:paragraph {"className":"pdf-hero-sub"} -->
			<p class="pdf-hero-sub"><?php esc_html_e( 'Independent special-education and public-accountability reporting. We pull the public record out of Massachusetts districts and put it where parents can use it.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
		</div>
		<!-- /wp:group -->

		<!-- wp:html -->
		<div class="pdf-hero-logo"><img src="<?php echo esc_url( $pdf_logo ); ?>" alt="<?php esc_attr_e( 'Parent Data Force — fault line logo', 'pdforce' ); ?>" width="380" height="380"></div>
		<!-- /wp:html -->
	</div>
	<!-- /wp:group -->
</section>
<!-- /wp:group -->
