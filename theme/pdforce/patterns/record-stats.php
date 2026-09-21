<?php
/**
 * Title: Record stats strip
 * Slug: pdforce/record-stats
 * Categories: pdforce_page, featured
 * Description: Data-driven strip showing live coverage of the Massachusetts
 *              Student Settlement Records Project (36 districts, 8 receipts).
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

// Live figures from the Student Settlement Records Project tracker
// (page: massachusetts-student-settlement-records-project). Update these
// whenever the tracker is refreshed; they describe real coverage, so keep
// them honest.
$pdf_stats = array(
	array( 'num' => '36',     'lbl' => __( 'Districts requested', 'pdforce' ) ),
	array( 'num' => '8',      'lbl' => __( 'Receipts acknowledged', 'pdforce' ) ),
	array( 'num' => '0',      'lbl' => __( 'Records published yet', 'pdforce' ) ),
	array( 'num' => 'Sept. 18, 2021–present', 'lbl' => __( 'Records window', 'pdforce' ), 'range' => true ),
);
?>
<!-- wp:group {"align":"full","className":"pdf-stats","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull pdf-stats">
	<!-- wp:html -->
	<div class="pdf-stats-grid">
		<?php foreach ( $pdf_stats as $pdf_s ) : ?>
			<div class="pdf-stat">
				<div class="pdf-stat-num<?php echo empty( $pdf_s['range'] ) ? '' : ' pdf-stat-num--range'; ?>"><?php echo esc_html( $pdf_s['num'] ); ?></div>
				<div class="pdf-stat-lbl"><?php echo esc_html( $pdf_s['lbl'] ); ?></div>
			</div>
		<?php endforeach; ?>
	</div>
	<!-- /wp:html -->
</div>
<!-- /wp:group -->
