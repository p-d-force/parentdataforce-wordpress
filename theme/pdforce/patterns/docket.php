<?php
/**
 * Title: Records docket
 * Slug: pdforce/docket
 * Categories: query
 * Block Types: core/query
 * Description: Posts rendered as a monospace public-records docket — date,
 *              scope, title + excerpt, and a record-reference count.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

?>
<!-- wp:query {"query":{"perPage":10,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","author":"","search":"","exclude":[],"sticky":"","inherit":true,"taxQuery":null,"parents":[]},"align":"wide","className":"pdf-docket","layout":{"type":"default"}} -->
<div class="wp-block-query alignwide pdf-docket">
	<!-- wp:post-template {"className":"pdf-docket-list"} -->
		<!-- wp:group {"className":"pdf-drow","layout":{"type":"flex","orientation":"horizontal","flexWrap":"wrap","verticalAlignment":"top"}} -->
		<div class="wp-block-group pdf-drow">
			<!-- wp:post-date {"format":"M j","className":"pdf-drow-date"} /-->
			<!-- wp:post-terms {"term":"category","separator":" · ","className":"pdf-drow-cat"} /-->
			<!-- wp:group {"className":"pdf-drow-main","layout":{"type":"default"}} -->
			<div class="wp-block-group pdf-drow-main">
				<!-- wp:post-title {"isLink":true,"level":3,"className":"pdf-drow-title"} /-->
				<!-- wp:post-excerpt {"moreText":"","excerptLength":28,"className":"pdf-drow-excerpt"} /-->
			</div>
			<!-- /wp:group -->
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

	<!-- wp:query-pagination {"paginationArrow":"arrow","align":"wide","layout":{"type":"flex","justifyContent":"space-between"}} -->
		<!-- wp:query-pagination-previous /-->
		<!-- wp:query-pagination-numbers /-->
		<!-- wp:query-pagination-next /-->
	<!-- /wp:query-pagination -->
</div>
<!-- /wp:query -->
