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
<!-- wp:group {"align":"full","className":"pdforce-navbar","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull pdforce-navbar">
	<!-- wp:group {"align":"wide","className":"pdforce-navbar__inner","style":{"spacing":{"padding":{"top":"var:preset|spacing|20","bottom":"var:preset|spacing|20"}}},"layout":{"type":"flex","flexWrap":"nowrap","justifyContent":"space-between","verticalAlignment":"center"}} -->
	<div class="wp-block-group alignwide pdforce-navbar__inner" style="padding-top:var(--wp--preset--spacing--20);padding-bottom:var(--wp--preset--spacing--20)">
		<!-- wp:group {"className":"pdforce-navbar__brand","layout":{"type":"flex","flexWrap":"nowrap","verticalAlignment":"center","blockGap":"var:preset|spacing|20"}} -->
		<div class="wp-block-group pdforce-navbar__brand">
			<!-- wp:image {"width":36,"aspectRatio":"1","scale":"contain","linkDestination":"none"} -->
			<figure class="wp-block-image is-resized"><img src="https://www.parentdataforce.com/wp-content/uploads/brand/logo.png" alt="Parent Data Force Logo" width="36" height="36" style="aspect-ratio:1;object-fit:contain"/></figure>
			<!-- /wp:image -->
			<!-- wp:site-title {"level":0} /-->
		</div>
		<!-- /wp:group -->
		<!-- wp:navigation {"overlayBackgroundColor":"base","overlayTextColor":"contrast","layout":{"type":"flex","justifyContent":"right","flexWrap":"nowrap"}} -->
		<!-- wp:navigation-link {"label":"Data","type":"custom","url":"https://www.parentdataforce.com/data/","kind":"custom","isTopLevelLink":true} -->
		<!-- wp:navigation-link {"label":"Data Browser","type":"custom","url":"https://www.parentdataforce.com/data/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Districts","type":"custom","url":"https://www.parentdataforce.com/districts/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Case Directory","type":"custom","url":"https://www.parentdataforce.com/cases/","kind":"custom"} /-->
		<!-- /wp:navigation-link -->
		<!-- wp:navigation-link {"label":"Records","type":"custom","url":"https://www.parentdataforce.com/projects/","kind":"custom","isTopLevelLink":true} -->
		<!-- wp:navigation-link {"label":"Projects","type":"custom","url":"https://www.parentdataforce.com/projects/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Massachusetts Student Settlement Records Project","type":"custom","url":"https://www.parentdataforce.com/massachusetts-student-settlement-records-project/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Worcester Cybersecurity Records Project","type":"custom","url":"https://www.parentdataforce.com/worcester-cybersecurity-records-project/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Weston Public Schools DEI Records Project","type":"custom","url":"https://www.parentdataforce.com/weston-dei-records-project/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Middleborough Principal-Hiring Records Project","type":"custom","url":"https://www.parentdataforce.com/middleborough-principal-hiring-records-project/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"East Bridgewater Public Schools Public Records Project","type":"custom","url":"https://www.parentdataforce.com/east-bridgewater-public-records-project/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Ways to Contribute","type":"custom","url":"https://www.parentdataforce.com/contribute/","kind":"custom"} /-->
		<!-- /wp:navigation-link -->
		<!-- wp:navigation-link {"label":"Writing","type":"custom","url":"https://www.parentdataforce.com/articles/","kind":"custom","isTopLevelLink":true} -->
		<!-- wp:navigation-link {"label":"Articles","type":"custom","url":"https://www.parentdataforce.com/articles/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"Appearances","type":"custom","url":"https://www.parentdataforce.com/appearances/","kind":"custom"} /-->
		<!-- /wp:navigation-link -->
		<!-- wp:navigation-link {"label":"About","type":"custom","url":"https://www.parentdataforce.com/about/","kind":"custom","isTopLevelLink":true} -->
		<!-- wp:navigation-link {"label":"Resources","type":"custom","url":"https://www.parentdataforce.com/resources/","kind":"custom"} /-->
		<!-- wp:navigation-link {"label":"About","type":"custom","url":"https://www.parentdataforce.com/about/","kind":"custom"} /-->
		<!-- /wp:navigation-link -->
		<!-- wp:navigation-link {"label":"\u2764 Donate","url":"https://www.parentdataforce.com/donate/"} /-->
		<!-- wp:navigation-link {"label":"Account","url":"/account/"} /-->
		<!-- wp:search {"label":"Search","showLabel":false,"placeholder":"Search the site…","buttonPosition":"button-position-outside","className":"pdforce-navsearch"} /-->
		<!-- /wp:navigation -->
	</div>
	<!-- /wp:group -->
</div>
<!-- /wp:group -->
