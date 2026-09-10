<?php
/**
 * Title: Article meta
 * Slug: pdforce/article-meta
 * Inserter: no
 * Description: Publication date, author and categories for long-form articles.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.0
 */

?>
<!-- wp:group {"style":{"spacing":{"blockGap":"0.5em","margin":{"bottom":"var:preset|spacing|40"}}},"fontSize":"small","layout":{"type":"flex","flexWrap":"wrap"}} -->
<div class="wp-block-group has-small-font-size" style="margin-bottom:var(--wp--preset--spacing--40)">
	<!-- wp:post-date {"style":{"color":{"text":"var:preset|color|accent-4"}}} /-->
	<!-- wp:paragraph {"style":{"color":{"text":"var:preset|color|accent-4"}}} -->
	<p class="has-text-color" style="color:var(--wp--preset--color--accent-4)">&middot;</p>
	<!-- /wp:paragraph -->
	<!-- wp:post-author-name {"isLink":true,"style":{"color":{"text":"var:preset|color|contrast"}}} /-->
	<!-- wp:paragraph {"style":{"color":{"text":"var:preset|color|accent-4"}}} -->
	<p class="has-text-color" style="color:var(--wp--preset--color--accent-4)"><?php esc_html_e( 'in', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->
	<!-- wp:post-terms {"term":"category","style":{"typography":{"fontWeight":"300"}}} /-->
</div>
<!-- /wp:group -->
