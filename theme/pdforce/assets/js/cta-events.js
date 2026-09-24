/**
 * Parent Data Force — sitewide CTA click tracking.
 *
 * Event-delegated click listener that categorizes link/button activations in
 * the main content area and reports them as GA4 `cta_click` events against
 * whatever gtag configs the page has (Site Kit's tag on WP pages, the head.php
 * G- tag on the static sections — same property either way).
 *
 * Excludes site chrome: theme header/footer template parts, nav menus, the
 * mobile nav toggle, and the settlement-tracker filter chips / search input.
 * No dependencies; loaded deferred in the footer on every public view.
 */
( function () {
	'use strict';

	var CHROME_SELECTOR =
		'header.wp-block-template-part, footer.wp-block-template-part, ' +
		'nav.nav, footer.footer, .pssr-chip, .pssr-search';

	function label( el ) {
		var raw =
			el.getAttribute( 'aria-label' ) ||
			( el.textContent || '' ).replace( /\s+/g, ' ' ).trim() ||
			el.getAttribute( 'title' ) ||
			el.getAttribute( 'href' ) ||
			'';
		raw = String( raw ).replace( /\s+/g, ' ' ).trim();
		return raw.length > 100 ? raw.slice( 0, 100 ) : raw;
	}

	function categorize( el ) {
		var href = el.getAttribute( 'href' ) || '';

		if ( 0 === href.indexOf( 'mailto:' ) ) {
			return 'email';
		}
		if ( /\.pdf([?#]|$)/i.test( href ) ) {
			return 'download';
		}
		if ( 0 === href.indexOf( 'http' ) && -1 === href.indexOf( 'parentdataforce.com' ) ) {
			return 'external';
		}
		if ( 0 === href.indexOf( '#' ) ) {
			return 'anchor';
		}
		if (
			'button' === el.tagName.toLowerCase() ||
			el.classList.contains( 'wp-block-button__link' ) ||
			el.classList.contains( 'btn' )
		) {
			return 'button';
		}
		return 'link';
	}

	document.addEventListener(
		'click',
		function ( ev ) {
			var el = ev.target.closest( 'a, button' );
			if ( ! el ) {
				return;
			}
			if ( el.closest( CHROME_SELECTOR ) ) {
				return;
			}

			var href = el.getAttribute( 'href' ) || '';
			if ( href.length > 300 ) {
				href = href.slice( 0, 300 );
			}

			var params = {
				cta_label: label( el ),
				cta_type: categorize( el ),
				cta_url: href
			};

			// Mirror into dataLayer first so tests can assert even when the
			// network beacon is blocked.
			window.dataLayer = window.dataLayer || [];
			window.dataLayer.push(
				Object.assign( { event: 'cta_click' }, params )
			);

			if ( typeof window.gtag === 'function' ) {
				window.gtag( 'event', 'cta_click', params );
			}
		},
		{ capture: true, passive: true }
	);
} )();
