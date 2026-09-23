<?php
/**
 * Title: Record stats strip
 * Slug: pdforce/record-stats
 * Categories: pdforce_page, featured
 * Description: Rotating data strip covering the Massachusetts Student
 *              Settlement Records Project. Sets crossfade every few seconds
 *              when JS is available; the first set renders statically
 *              without it.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

// Live figures from the Student Settlement Records Project tracker
// (page: massachusetts-student-settlement-records-project). Update BOTH sets
// whenever the tracker is refreshed; they describe real coverage, so keep
// them honest.
$pdf_stat_sets = array(
	// Set 1 — the project at a glance.
	array(
		array( 'num' => '65', 'lbl' => __( 'Districts requested', 'pdforce' ) ),
		array( 'num' => '14', 'lbl' => __( 'Receipts acknowledged', 'pdforce' ) ),
		array( 'num' => '0', 'lbl' => __( 'Records published yet', 'pdforce' ) ),
		array( 'num' => 'Sept. 18, 2021–present', 'lbl' => __( 'Records window', 'pdforce' ), 'range' => true ),
	),
	// Set 2 — where each district stands right now.
	array(
		array( 'num' => '45', 'lbl' => __( 'Awaiting first response', 'pdforce' ) ),
		array( 'num' => '5', 'lbl' => __( 'Routed or re-sent', 'pdforce' ) ),
		array( 'num' => '1', 'lbl' => __( 'SPR appeal filed', 'pdforce' ) ),
		array( 'num' => 'Oct. 2–7', 'lbl' => __( 'Response milestones', 'pdforce' ), 'range' => true ),
	),
);
?>
<!-- wp:group {"align":"full","className":"pdf-stats","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull pdf-stats">
	<!-- wp:html -->
	<div class="pdf-stats-grid">
		<?php foreach ( $pdf_stat_sets as $pdf_i => $pdf_set ) : ?>
			<div class="pdf-stats-set<?php echo $pdf_i ? ' is-hidden' : ''; ?>"<?php echo $pdf_i ? ' aria-hidden="true"' : ''; ?>>
				<?php foreach ( $pdf_set as $pdf_s ) : ?>
					<div class="pdf-stat">
						<div class="pdf-stat-num<?php echo empty( $pdf_s['range'] ) ? '' : ' pdf-stat-num--range'; ?>"><?php echo esc_html( $pdf_s['num'] ); ?></div>
						<div class="pdf-stat-lbl"><?php echo esc_html( $pdf_s['lbl'] ); ?></div>
					</div>
				<?php endforeach; ?>
			</div>
		<?php endforeach; ?>
	</div>
	<div class="pdf-stats-dots" role="presentation">
		<?php foreach ( $pdf_stat_sets as $pdf_i => $pdf_set ) : ?>
			<button type="button" class="pdf-stats-dot<?php echo 0 === $pdf_i ? ' is-active' : ''; ?>" data-set="<?php echo esc_attr( $pdf_i ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Show stats set %d', 'pdforce' ), $pdf_i + 1 ) ); ?>"></button>
		<?php endforeach; ?>
	</div>
	<!-- /wp:html -->
</div>
<!-- /wp:group -->