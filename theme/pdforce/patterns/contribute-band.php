<?php
/**
 * Title: Ways to contribute band
 * Slug: pdforce/contribute-band
 * Categories: pdforce_page, featured
 * Block Types: core/group
 * Description: Compact homepage band with the three highest-leverage ways to
 *              help — donate, send documents, speak at public comment.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.14
 */

?>
<!-- wp:group {"tagName":"section","align":"wide","className":"pdf-contrib-band pdf-band","layout":{"type":"default"}} -->
<section class="wp-block-group alignwide pdf-contrib-band pdf-band">
	<!-- wp:paragraph {"className":"pdf-kicker"} -->
	<p class="pdf-kicker"><?php esc_html_e( 'Ways to help', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->

	<!-- wp:heading {"level":2,"fontSize":"x-large"} -->
	<h2 class="has-x-large-font-size"><?php esc_html_e( 'Fund it, document it, or say it out loud.', 'pdforce' ); ?></h2>
	<!-- /wp:heading -->

	<!-- wp:group {"className":"pdf-contrib-grid","layout":{"type":"default"}} -->
	<div class="wp-block-group pdf-contrib-grid">
		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Fund', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Donate', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'One-time or monthly, it pays the copying fees and filing costs that decide whether a district hands over its records or bills you for them.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/donate/"><?php esc_html_e( 'Donate →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Records', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Submit documents and data', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'A settlement agreement, an IEP, a placement decision, a fee letter, minutes from a meeting. Send the document and we will use it in an appeal or publish it in the tracker.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/submit/#upload"><?php esc_html_e( 'Upload documents →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Speak', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Speak at public comment', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'Two minutes on the record at your school committee meeting is public documentation. We will help you write it.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/contribute/#public-comment"><?php esc_html_e( 'Prepare your remarks →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->
	</div>
	<!-- /wp:group -->

	<!-- wp:paragraph -->
	<p><a href="https://www.parentdataforce.com/contribute/"><?php esc_html_e( 'All six ways to help →', 'pdforce' ); ?></a></p>
	<!-- /wp:paragraph -->
</section>
<!-- /wp:group -->