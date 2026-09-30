<?php
/**
 * Title: Header
 * Slug: pdforce/header
 * Categories: header
 * Block Types: core/template-part/header
 * Description: Site header with logo, site title and navigation.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.0
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
				<figure class="wp-block-image is-resized"><img src="https://www.parentdataforce.com/wp-content/uploads/brand/logo.png" alt="Parent Data Force Logo" width="80" height="80" style="aspect-ratio:1;object-fit:contain;border-radius:8px"/></figure>
				<!-- /wp:image -->
				<!-- wp:site-title {"level":0} /-->
			</div>
			<!-- /wp:group -->
			<!-- wp:group {"style":{"spacing":{"blockGap":"var:preset|spacing|10"}},"layout":{"type":"flex","flexWrap":"nowrap","justifyContent":"right"}} -->
			<div class="wp-block-group">
	<!-- wp:navigation {"overlayBackgroundColor":"base","overlayTextColor":"contrast","layout":{"type":"flex","justifyContent":"right","flexWrap":"wrap"}} -->
			<!-- wp:navigation-link {"label":"Data","url":"https://www.parentdataforce.com/data/"} /-->
			<!-- wp:navigation-link {"label":"Districts","url":"https://www.parentdataforce.com/districts/"} /-->
			<!-- wp:navigation-link {"label":"Projects","url":"https://www.parentdataforce.com/projects/"} /-->
			<!-- wp:navigation-link {"label":"Articles","url":"https://www.parentdataforce.com/articles/"} /-->
			<!-- wp:navigation-link {"label":"Appearances","url":"https://www.parentdataforce.com/appearances/"} /-->
			<!-- wp:navigation-link {"label":"Resources","url":"https://www.parentdataforce.com/resources/"} /-->
			<!-- wp:navigation-link {"label":"About","url":"https://www.parentdataforce.com/about/"} /-->
			<!-- wp:navigation-link {"label":"\u2764 Donate","url":"https://www.parentdataforce.com/donate/"} /-->
			<!-- wp:navigation-link {"label":"Account","url":"/account/"} /-->
			<!-- wp:search {"label":"Search","showLabel":false,"placeholder":"Search the site…","buttonPosition":"no-button","className":"pdforce-navsearch"} /-->
			<!-- /wp:navigation -->
			</div>
			<!-- /wp:group -->
		</div>
		<!-- /wp:group -->
	</div>
	<!-- /wp:group -->
</div>
<!-- /wp:group -->
