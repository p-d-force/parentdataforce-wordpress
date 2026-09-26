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
		// Hostname comparison rather than a substring test: share-sharer URLs
		// embed an ENCODED copy of the current permalink (u=https%3A%2F%2Fwww
		// .parentdataforce.com/...), which the plain-text test would mistake
		// for an internal link.
		if (
			0 === href.indexOf( 'http' ) &&
			el.hostname &&
			el.hostname !== window.location.hostname
		) {
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

	/* Copy-link buttons (.pdf-share-copy): copy the permalink, then briefly
	   swap the label to "Copied" so the action is visible. */
	document.addEventListener(
		'click',
		function ( ev ) {
			var btn = ev.target.closest( '.pdf-share-copy' );
			if ( ! btn ) {
				return;
			}

			var url = btn.getAttribute( 'data-share-url' ) || '';
			if ( ! url ) {
				return;
			}

			function done() {
				var original = btn.textContent;
				btn.textContent = 'Copied';
				setTimeout( function () {
					btn.textContent = original;
				}, 1500 );
			}

			if ( navigator.clipboard && navigator.clipboard.writeText ) {
				navigator.clipboard.writeText( url ).then( done ).catch( function () {
					legacyCopy( url );
					done();
				} );
			} else {
				legacyCopy( url );
				done();
			}
		},
		{ capture: true }
	);

	function legacyCopy( text ) {
		var ta = document.createElement( 'textarea' );
		ta.value = text;
		ta.setAttribute( 'readonly', '' );
		ta.style.position = 'fixed';
		ta.style.left = '-9999px';
		document.body.appendChild( ta );
		ta.select();
		try {
			document.execCommand( 'copy' );
		} catch ( e ) {} // eslint-disable-line no-empty
		document.body.removeChild( ta );
	}
} )();
