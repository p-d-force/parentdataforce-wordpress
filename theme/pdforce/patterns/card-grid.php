<?php
/**
 * Title: Record card grid
 * Slug: pdforce/card-grid
 * Categories: query, pdforce_page
 * Block Types: core/query
 * Description: The six newest posts as hairline-separated cards — category
 *              tag, linked title, date and excerpt, and a read link. The
 *              query does not inherit the page query, so this grid always
 *              shows the same six newest records on every page.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.14
 */

?>
<!-- wp:query {"query":{"perPage":6,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","author":"","search":"","exclude":[],"sticky":"","inherit":false,"taxQuery":null,"parents":[]},"align":"wide","className":"pdf-docket","layout":{"type":"default"}} -->
<div class="wp-block-query alignwide pdf-docket">
	<!-- wp:post-template {"className":"pdf-cardgrid"} -->
		<!-- wp:group {"className":"pdf-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card">
			<!-- wp:post-terms {"term":"category","className":"pdf-card-tag"} /-->
			<!-- wp:post-title {"isLink":true,"level":3,"className":"pdf-card-title"} /-->
			<!-- wp:post-date {"format":"M j, Y","className":"pdf-card-meta"} /-->
			<!-- wp:post-excerpt {"moreText":"","excerptLength":26,"className":"pdf-card-excerpt"} /-->
			<!-- wp:html -->
			<a class="pdf-card-read" href="<?php echo esc_url( get_permalink() ); ?>"><?php esc_html_e( 'Read the record →', 'pdforce' ); ?></a>
			<!-- /wp:html -->
		</div>
		<!-- /wp:group -->
	<!-- /wp:post-template -->

	<!-- wp:query-no-results -->
		<!-- wp:paragraph {"className":"pdf-kicker"} -->
		<p class="pdf-kicker"><?php esc_html_e( 'No records found', 'pdforce' ); ?></p>
		<!-- /wp:paragraph -->
		<!-- wp:paragraph -->
		<p><?php esc_html_e( 'Nothing filed under this heading yet. New records are added as they are pulled and verified.', 'pdforce' ); ?></p>
		<!-- /wp:paragraph -->
	<!-- /wp:query-no-results -->
</div>
<!-- /wp:query -->