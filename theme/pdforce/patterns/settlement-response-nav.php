<?php
/**
 * Title: Settlement response series nav
 * Slug: pdforce/settlement-response-nav
 * Inserter: no
 * Description: Cross-links the district-response articles in the Student Settlement Records Project series. Renders only on District Data posts.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

if ( ! is_singular( 'post' ) || ! has_category( array( 'District Data' ) ) ) {
	return;
}

$pdforce_series_slug = get_post_field( 'post_name' );
$pdforce_series      = array(
	'tantasqua-first-production-45-pages-no-fee'      => 'Tantasqua Regional — first production: 45 pages, no fee',
	'dracut-charges-2950-for-45-agreements'           => 'Dracut — $2,950 for 45 agreements it won\'t show',
	'peabody-wants-300-before-it-looks'               => 'Peabody — $300 before the search starts',
	'pentucket-itemizes-150-estimate'                 => 'Pentucket — $150, itemized to the half-hour',
	'berlin-boylston-prices-request-at-75-denies-waiver' => 'Berlin-Boylston — $75 itemized, fee waiver denied',
	'amesbury-750-fee-estimate-under-appeal'          => 'Amesbury — $750 fee estimate, appealed to the Supervisor of Records',
);
?>
<!-- wp:group {"layout":{"type":"constrained"}} -->
<div class="wp-block-group">
	<!-- wp:heading {"level":2} -->
	<h2><?php esc_html_e( 'Every district response, in one place', 'pdforce' ); ?></h2>
	<!-- /wp:heading -->
	<!-- wp:html -->
	<ul class="pdf-response-nav">
		<?php foreach ( $pdforce_series as $pdforce_series_slug_i => $pdforce_series_label ) : ?>
			<?php $pdforce_series_url = 'https://www.parentdataforce.com/' . $pdforce_series_slug_i . '/'; ?>
			<li<?php echo ( $pdforce_series_slug_i === $pdforce_series_slug ) ? ' class="is-current"' : ''; ?>><a href="<?php echo esc_url( $pdforce_series_url ); ?>"><?php echo esc_html( $pdforce_series_label ); ?></a></li>
		<?php endforeach; ?>
		<li><a href="https://www.parentdataforce.com/massachusetts-student-settlement-records-project/"><?php esc_html_e( 'The live tracker — all 65 districts, fees, and records', 'pdforce' ); ?></a></li>
	</ul>
	<!-- /wp:html -->
</div>
<!-- /wp:group -->
