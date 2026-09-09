<?php
/**
 * Title: Header
 * Slug: twentytwentyfive/header
 * Categories: header
 * Block Types: core/template-part/header
 * Description: Site header with logo, site title and navigation.
 *
 * @package WordPress
 * @subpackage Twenty_Twenty_Five
 * @since Twenty Twenty-Five 1.0
 */

?>
<!-- wp:group {"align":"full","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull">
	<!-- wp:group {"layout":{"type":"constrained"}} -->
	<div class="wp-block-group">
		<!-- wp:group {"align":"wide","style":{"spacing":{"padding":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|30"}}},"layout":{"type":"flex","flexWrap":"nowrap","justifyContent":"space-between"}} -->
		<div class="wp-block-group alignwide" style="padding-top:var(--wp--preset--spacing--30);padding-bottom:var(--wp--preset--spacing--30)">
			<!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap","alignItems":"center","blockGap":"var:preset|spacing|12"}} -->
			<div class="wp-block-group">
				<!-- wp:image {"width":80,"aspectRatio":"1","scale":"contain","linkDestination":"none","style":{"border":{"radius":"8px"}}} -->
				<figure class="wp-block-image is-resized"><img src="https://www.parentdataforce.com/wordpress/wp-content/uploads/brand/logo.png" alt="Parent Data Force Logo" width="80" height="80" style="aspect-ratio:1;object-fit:contain;border-radius:8px"/></figure>
				<!-- /wp:image -->
				<!-- wp:site-title {"level":0} /-->
			</div>
			<!-- /wp:group -->
			<!-- wp:group {"style":{"spacing":{"blockGap":"var:preset|spacing|10"}},"layout":{"type":"flex","flexWrap":"nowrap","justifyContent":"right"}} -->
			<div class="wp-block-group">
				<!-- wp:navigation {"overlayBackgroundColor":"base","overlayTextColor":"contrast","layout":{"type":"flex","justifyContent":"right","flexWrap":"wrap"}} /-->
			</div>
			<!-- /wp:group -->
		</div>
		<!-- /wp:group -->
	</div>
	<!-- /wp:group -->
</div>
<!-- /wp:group -->
