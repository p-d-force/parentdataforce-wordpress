<?php
/**
 * Title: Record stats strip
 * Slug: pdforce/record-stats
 * Categories: pdforce_page, featured
 * Description: Data-driven strip showing live public-record coverage pulled
 *              from the district scraper (445 districts, meetings, minutes).
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

// Live figures from the district scraper (Scrapers/data). Update these as the
// scrape grows; they describe real coverage, so keep them honest.
$pdf_stats = array(
	array( 'num' => '445',     'lbl' => __( 'Districts tracked', 'pdforce' ) ),
	array( 'num' => '251',     'lbl' => __( 'Meetings indexed', 'pdforce' ) ),
	array( 'num' => '31',      'lbl' => __( 'Minute sets pulled', 'pdforce' ) ),
	array( 'num' => '’25–’27', 'lbl' => __( 'Record span', 'pdforce' ) ),
);
?>
<!-- wp:group {"align":"full","className":"pdf-stats","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull pdf-stats">
	<!-- wp:html -->
	<div class="pdf-stats-grid">
		<?php foreach ( $pdf_stats as $pdf_s ) : ?>
			<div class="pdf-stat">
				<div class="pdf-stat-num"><?php echo esc_html( $pdf_s['num'] ); ?></div>
				<div class="pdf-stat-lbl"><?php echo esc_html( $pdf_s['lbl'] ); ?></div>
			</div>
		<?php endforeach; ?>
	</div>
	<!-- /wp:html -->
</div>
<!-- /wp:group -->
