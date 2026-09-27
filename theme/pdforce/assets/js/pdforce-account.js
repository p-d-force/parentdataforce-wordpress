/**
 * Parent Data Force — member account front-end.
 *
 * Vanilla JS, no dependencies. Mounts into whatever #pdforce-account-root
 * exists on one of the six account pages (body class is_page-account /
 * -register / -login / -ticket / -confirm / -reset set by the mu-plugin)
 * and drives comment gating hints on single posts.
 *
 * All state comes from pdforceAccount (wp_localize_script by the
 * pdforce-account mu-plugin): page, restUrl, loggedIn, wpNonce,
 * accountUrl, registerUrl, loginUrl, ticketUrl, confirmUrl, resetUrl.
 *
 * Security properties:
 *  - Registration and login ALWAYS send honeypot (pdforce_website) + a
 *    fresh timestamp (pdforce_ts) so replayed bot posts die at the gate.
 *  - Session rides WordPress cookies; every authenticated REST call
 *    carries the X-WP-Nonce header issued at login/refresh time.
 *  - Only same-origin redirect targets from the server are followed.
 *  - All server-supplied strings land via textContent — never innerHTML.
 */
( function () {
	'use strict';

	var CFG   = window.pdforceAccount;
	var ROOT  = document.getElementById( 'pdforce-account-root' );
	var DAY   = 86400000;
	var reloaded = false; // one-shot stale-nonce reload guard

	if ( ! CFG ) {
		return;
	}

	/* ---------- helpers ---------- */

	function el( tag, attrs, text ) {
		var n = document.createElement( tag );
		if ( attrs ) {
			for ( var k in attrs ) {
				if ( Object.prototype.hasOwnProperty.call( attrs, k ) ) {
					if ( 'className' === k ) {
						n.className = attrs[ k ];
					} else if ( 'text' === k ) {
						n.textContent = attrs[ k ];
					} else if ( k.indexOf( 'data-' ) === 0 ) {
						n.setAttribute( k, attrs[ k ] );
					} else if ( k.indexOf( 'on' ) === 0 ) {
						n.addEventListener( k.slice( 2 ).toLowerCase(), attrs[ k ] );
					} else {
						n.setAttribute( k.replace( /[A-Z]/g, function ( c ) { return '-' + c.toLowerCase(); } ), attrs[ k ] );
					}
				}
			}
		}
		if ( text ) {
			n.textContent = text;
		}
		return n;
	}

	function stamp() {
		return {
			pdforce_website: '',
			pdforce_ts: Math.floor( Date.now() / 1000 )
		};
	}

	function msg( elMsg, kind, text ) {
		elMsg.className = 'pdex-msg on ' + kind;
		elMsg.textContent = text;
	}

	function busy( form, on ) {
		var b = form.querySelector( 'button[type="submit"]' );
		if ( b ) {
			b.disabled = !! on;
		}
	}

	function api( path, opts, nonce ) {
		opts = opts || {};
		var headers = { 'Accept': 'application/json' };
		if ( opts.body ) {
			headers[ 'Content-Type' ] = 'application/json';
		}
		if ( nonce ) {
			headers[ 'X-WP-Nonce' ] = nonce;
		}
		return fetch( CFG.restUrl.replace( /\/$/, '' ) + path, {
			method: opts.method || 'POST',
			credentials: 'same-origin',
			headers: headers,
			body: opts.body ? JSON.stringify( opts.body ) : undefined
		} ).then( function ( r ) {
			return r.json().then( function ( j ) {
				if ( r.status === 403 && j && j.code === 'rest_cookie_invalid_nonce' && ! reloaded ) {
					// Session token was cycled server-side (stale nonce).
					// One clean reload re-fetches state; park the caller
					// on a never-resolving promise so the stale response
					// is never processed as an error.
					reloaded = true;
					window.location.reload();
					return new Promise( function () {} );
				}
				return { status: r.status, json: j || {} };
			} );
		} );
	}

	function authed() {
		return CFG.loggedIn && CFG.wpNonce;
	}

	function fmtDate( iso ) {
		try {
			var d = new Date( iso );
			return d.toLocaleDateString( undefined, { month: 'short', day: 'numeric', year: 'numeric' } );
		} catch ( e ) {
			return iso;
		}
	}

	function headerBadge() {
		// Logged-in visitors: header "Account" link becomes "My account".
		var links = document.querySelectorAll(
			'.wp-block-navigation-link a[href*="/account"]'
		);
		for ( var i = 0; i < links.length; i++ ) {
			if ( authed() && links[ i ].textContent.trim().toLowerCase() === 'account' ) {
				links[ i ].textContent = 'My account';
			}
		}
	}

	/* ---------- single-post comment gate hint ---------- */

	function mountCommentsHint() {
		// Core renders the .must-log-in notice for anonymous visitors; the
		// only job here is pointing its link at our styled login page
		// (preserving the redirect back to this article). No extra panel:
		// logged-in users get the real form from core.
		// Singles are localized with page:'' (only the six account pages
		// carry a sentinel), so an empty page means we are on a post.
		if ( CFG.page || authed() ) {
			return;
		}
		var a = document.querySelector( '.must-log-in a' );
		if ( a ) {
			a.href = CFG.loginUrl + '?redirect_to=' + encodeURIComponent( location.pathname + location.search );
		}
	}

	/* ---------- forms ---------- */

	function showMsg( root, text, kind ) {
		var m = root.querySelector( '.pdex-msg' );
		if ( m ) {
			msg( m, kind || 'err', text );
		}
	}

	function mountForm( kind ) {
		// kind: 'register' | 'login'
		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' },
			'register' === kind ? 'Parent Data Force members' : 'Welcome back' ) );

		var form = el( 'form', { novalidate: true } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );

		function row( labelText, inputAttrs, wrapCls ) {
			var w = el( 'div', { className: wrapCls || 'pdex-row' } );
			var id = 'pdex-' + inputAttrs.name;
			var lab = el( 'label', { for: id }, labelText );
			inputAttrs.id = id;
			w.appendChild( lab );
			w.appendChild( el( 'input', inputAttrs ) );
			return w;
		}

		if ( 'register' === kind ) {
			var split = el( 'div', { className: 'pdex-row-split' } );
			split.appendChild( row( 'Email', { type: 'email', name: 'user_email', autocomplete: 'email', required: true } ) );
			split.appendChild( row( 'Display name (optional)', { type: 'text', name: 'display_name' } ) );
			form.appendChild( split );
			form.appendChild( row( 'Password (8+ characters)', { type: 'password', name: 'password', autocomplete: 'new-password', required: true, minlength: 8 } ) );

			var roles = [ 'parent', 'educator', 'advocate', 'other' ];
			var w = el( 'div', { className: 'pdex-row' } );
			w.appendChild( el( 'label', { for: 'pdex-role' }, 'I am a… (optional, private)' ) );
			var sel = el( 'select', { id: 'pdex-role', name: 'pdforce_role' } );
			[ '', 'parent', 'educator', 'advocate', 'other' ].forEach( function ( r ) {
				sel.appendChild( el( 'option', { value: r }, roles.indexOf( r ) > -1 ? r.charAt(0).toUpperCase() + r.slice(1) : 'Prefer not to say' ) );
			} );
			w.appendChild( sel );
			form.appendChild( w );
			form.appendChild( row( 'School district (optional, private — helps route your question)', { type: 'text', name: 'pdforce_district' } ) );
		} else {
			form.appendChild( row( 'Username or email', { type: 'text', name: 'log', autocomplete: 'username', required: true } ) );
			form.appendChild( row( 'Password', { type: 'password', name: 'pwd', autocomplete: 'current-password', required: true } ) );
			var rem = el( 'div', { className: 'pdex-row' } );
			var cb = el( 'input', { type: 'checkbox', id: 'pdex-remember', name: 'remember' } );
			rem.appendChild( cb );
			rem.appendChild( el( 'label', { for: 'pdex-remember' }, 'Stay logged in for two weeks' ) );
			form.appendChild( rem );
		}

		// honeypot field: visually and screen-reader hidden, targeted at bots
		var hp = el( 'div', { className: 'pdex-row', style: 'position:absolute;left:-9999px;top:-9999px', 'aria-hidden': 'true' } );
		hp.appendChild( el( 'label', { for: 'pdex-website' }, 'Leave this field empty' ) );
		hp.appendChild( el( 'input', { type: 'text', name: 'pdforce_website', id: 'pdex-website', tabindex: '-1', autocomplete: 'off' } ) );
		form.appendChild( hp );

		form.appendChild( msgBox );
		var btn = el( 'button', { type: 'submit' }, 'register' === kind ? 'Create my account' : 'Log in' );
		form.appendChild( btn );
		root.appendChild( form );

		// swap link
		var swap = el( 'p', { className: 'pdex-swap' } );
		if ( 'register' === kind ) {
			swap.appendChild( document.createTextNode( 'Already have an account? ' ) );
			swap.appendChild( el( 'a', { href: CFG.loginUrl }, 'Log in' ) );
		} else {
			swap.appendChild( document.createTextNode( 'New to Parent Data Force? ' ) );
			swap.appendChild( el( 'a', { href: CFG.registerUrl }, 'Create an account' ) );
		}
		root.appendChild( swap );
		if ( 'login' === kind ) {
			var forgot = el( 'p', { className: 'pdex-swap' } );
			forgot.appendChild( el( 'a', { href: CFG.resetUrl }, 'Forgot your password?' ) );
			root.appendChild( forgot );
		}
		ROOT.appendChild( root );

		form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( form, true );
			msg( msgBox, '', '' );

			var payload = stamp();
			payload.redirect_to = new URLSearchParams( window.location.search ).get( 'redirect_to' ) || CFG.accountUrl;
			if ( 'register' === kind ) {
				payload.user_email = form.elements[ 'user_email' ].value;
				payload.password = form.elements[ 'password' ].value;
				payload.display_name = form.elements[ 'display_name' ].value;
				payload.pdforce_role = form.elements[ 'pdforce_role' ].value;
				payload.pdforce_district = form.elements[ 'pdforce_district' ].value;
			} else {
				payload.log = form.elements[ 'log' ].value;
				payload.pwd = form.elements[ 'pwd' ].value;
				payload.remember = cb.checked;
			}

			api( '/pdforce/v1/' + kind, { body: payload } ).then( function ( res ) {
				if ( res.status >= 400 ) {
					busy( form, false );
					showMsg( form, ( res.json.data && res.json.data.message ) || 'That did not work. Try again.' );
					return;
				}
				if ( 'register' === kind ) {
					// Hard confirmation gate: no session until the email
					// link is clicked. Swap the form for the check-your-
					// email panel with a resend button.
					while ( ROOT.firstChild ) {
						ROOT.removeChild( ROOT.firstChild );
					}
					renderCheckEmail( ( res.json.data && res.json.data.email ) || payload.user_email );
					return;
				}
				CFG.loggedIn = true;
				CFG.wpNonce = res.json.data && res.json.data.nonce || '';
				var to = ( res.json.data && res.json.data.redirect_to ) || CFG.accountUrl;
				// The server may echo a same-host PATH; resolve it so the
				// origin check below passes. Foreign origins still fail.
				if ( to && '/' === to.charAt( 0 ) ) {
					to = window.location.origin + to;
				}
				if ( to && to.indexOf( window.location.origin ) === 0 ) {
					window.location.href = to;
				}
			} ).catch( function () {
				busy( form, false );
				showMsg( form, 'Network error. Try again.' );
			} );
		} );
	}

	/* ---------- email confirmation + reset ---------- */

	/** Resend button wired to /pdforce/v1/resend; server text surfaces as-is. */
	function resendButton( email, msgBox ) {
		var btn = el( 'button', { type: 'button', className: 'pdex-quiet' }, 'Resend the link' );
		btn.addEventListener( 'click', function () {
			btn.disabled = true;
			msg( msgBox, '', '' );
			api( '/pdforce/v1/resend', { body: Object.assign( {}, stamp(), { email: email } ) } )
				.then( function ( r ) {
					btn.disabled = false;
					msg( msgBox, r.status === 429 ? 'err' : 'ok',
						( r.json.data && r.json.data.message ) ||
						( r.status === 429 ? 'Too many requests. Try again soon.'
							: 'If that email still needs confirming, a fresh link is on its way.' ) );
				} )
				.catch( function () {
					btn.disabled = false;
					msg( msgBox, 'err', 'Network error. Try again.' );
				} );
		} );
		return btn;
	}

	/** 'Check your email' terminal panel after registration. */
	function renderCheckEmail( email ) {
		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'Almost there' ) );
		var panel = el( 'div', { className: 'pdex-panel' } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
		panel.appendChild( msgBox );
		panel.appendChild( el( 'p', { style: 'margin:0 0 0.9rem' },
			'Click the confirmation link we just sent to ' + email + '. It expires in 48 hours.' ) );
		panel.appendChild( resendButton( email, msgBox ) );
		root.appendChild( panel );
		var swap = el( 'p', { className: 'pdex-swap' } );
		swap.appendChild( document.createTextNode( 'Signed up by mistake? ' ) );
		swap.appendChild( el( 'a', { href: CFG.loginUrl }, 'Log in' ) );
		root.appendChild( swap );
		ROOT.appendChild( root );
	}

	/** /account/confirm/?key=…&login=… — auto-submits the confirm call. */
	function mountConfirm() {
		var q = new URLSearchParams( window.location.search );
		var key = q.get( 'key' ) || '';
		var login = q.get( 'login' ) || '';

		function renderResend( text ) {
			while ( ROOT.firstChild ) {
				ROOT.removeChild( ROOT.firstChild );
			}
			var root = el( 'div', { className: 'pdex' } );
			root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'That link did not work' ) );
			var panel = el( 'div', { className: 'pdex-panel' } );
			panel.appendChild( el( 'div', { className: 'pdex-msg on err', text: text } ) );
			var row = el( 'div', { className: 'pdex-row' } );
			row.appendChild( el( 'label', { for: 'pdex-cf-email' }, 'Your email address' ) );
			var email = el( 'input', { type: 'email', id: 'pdex-cf-email', autocomplete: 'email', required: true } );
			row.appendChild( email );
			panel.appendChild( row );
			var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
			panel.appendChild( msgBox );
			panel.appendChild( resendButton( email.value, msgBox ) );
			root.appendChild( panel );
			var swap = el( 'p', { className: 'pdex-swap' } );
			swap.appendChild( document.createTextNode( 'Confirmed already? ' ) );
			swap.appendChild( el( 'a', { href: CFG.loginUrl }, 'Log in' ) );
			root.appendChild( swap );
			ROOT.appendChild( root );
			email.focus();
		}

		if ( ! key || ! login ) {
			// Landed without link params: offer the resend recovery path.
			renderResend( 'This page needs the link from your confirmation email. Enter your email and we will send a fresh one.' );
			return;
		}

		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'One click' ) );
		root.appendChild( el( 'p', { className: 'pdex-t-meta', style: 'margin:0.4rem 0' }, 'Confirming your account…' ) );
		ROOT.appendChild( root );

		api( '/pdforce/v1/confirm', { body: Object.assign( {}, stamp(), { key: key, login: login } ) } )
			.then( function ( r ) {
				if ( r.status === 400 ) {
					renderResend( ( r.json.data && r.json.data.message ) || 'That confirm link is invalid or expired. Send it again.' );
					return;
				}
				var d = r.json && r.json.data;
				if ( d && d.already ) {
					window.location.href = CFG.loginUrl;
					return;
				}
				if ( r.status < 400 && d ) {
					CFG.loggedIn = true;
					CFG.wpNonce = d.nonce || '';
					var to = d.redirect_to || CFG.accountUrl;
					if ( to && '/' === to.charAt( 0 ) ) {
						to = window.location.origin + to;
					}
					if ( to && to.indexOf( window.location.origin ) === 0 ) {
						window.location.href = to;
					}
					return;
				}
				renderResend( 'That confirm link is invalid or expired. Send it again.' );
			} )
			.catch( function () {
				renderResend( 'Network error — check your connection and use the link again.' );
			} );
	}

	/** /account/reset/ — request form without params; set-password with them. */
	function mountReset() {
		var q = new URLSearchParams( window.location.search );
		var key = q.get( 'key' ) || '';
		var login = q.get( 'login' ) || '';

		if ( ! key || ! login ) {
			var root = el( 'div', { className: 'pdex' } );
			root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'Reset your password' ) );
			var form = el( 'form', { novalidate: true } );
			var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
			var row = el( 'div', { className: 'pdex-row' } );
			row.appendChild( el( 'label', { for: 'pdex-fg-email' }, 'Your email address' ) );
			var email = el( 'input', { type: 'email', id: 'pdex-fg-email', autocomplete: 'email', required: true } );
			row.appendChild( email );
			form.appendChild( msgBox );
			form.appendChild( row );
			form.appendChild( el( 'button', { type: 'submit' }, 'Send reset link' ) );
			root.appendChild( form );
			var swap = el( 'p', { className: 'pdex-swap' } );
			swap.appendChild( document.createTextNode( 'Remembered it? ' ) );
			swap.appendChild( el( 'a', { href: CFG.loginUrl }, 'Log in' ) );
			root.appendChild( swap );
			ROOT.appendChild( root );

			form.addEventListener( 'submit', function ( ev ) {
				ev.preventDefault();
				busy( form, true );
				api( '/pdforce/v1/forgot', { body: Object.assign( {}, stamp(), { email: email.value } ) } )
					.then( function ( r ) {
						busy( form, false );
						if ( r.status < 400 || r.status === 429 ) {
							// 200 and 429 both surface the server's wording.
							msg( msgBox, r.status === 429 ? 'err' : 'ok',
								( r.json.data && r.json.data.message ) || 'If an account exists for that email, a reset link is on its way.' );
							return;
						}
						msg( msgBox, 'err', ( r.json.data && r.json.data.message ) || 'That did not work. Try again.' );
					} )
					.catch( function () {
						busy( form, false );
						msg( msgBox, 'err', 'Network error. Try again.' );
					} );
			} );
			return;
		}

		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'Choose a new password' ) );
		var form = el( 'form', { novalidate: true } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
		var r1 = el( 'div', { className: 'pdex-row' } );
		r1.appendChild( el( 'label', { for: 'pdex-rs-pw' }, 'New password (8+ characters)' ) );
		var pw = el( 'input', { type: 'password', id: 'pdex-rs-pw', autocomplete: 'new-password', required: true, minlength: 8 } );
		r1.appendChild( pw );
		var r2 = el( 'div', { className: 'pdex-row' } );
		r2.appendChild( el( 'label', { for: 'pdex-rs-pw2' }, 'Repeat it' ) );
		var pw2 = el( 'input', { type: 'password', id: 'pdex-rs-pw2', autocomplete: 'new-password', required: true, minlength: 8 } );
		r2.appendChild( pw2 );
		form.appendChild( msgBox );
		form.appendChild( r1 );
		form.appendChild( r2 );
		form.appendChild( el( 'button', { type: 'submit' }, 'Save new password' ) );
		root.appendChild( form );
		var again = el( 'p', { className: 'pdex-swap' } );
		again.appendChild( el( 'a', { href: window.location.pathname }, 'Send a new reset link' ) );
		root.appendChild( again );
		ROOT.appendChild( root );

		form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( form, true );
			if ( pw.value.length < 8 ) {
				busy( form, false );
				msg( msgBox, 'err', 'Password must be at least 8 characters.' );
				return;
			}
			if ( pw.value !== pw2.value ) {
				busy( form, false );
				msg( msgBox, 'err', 'The two passwords do not match.' );
				return;
			}
			api( '/pdforce/v1/password-reset', {
				body: Object.assign( {}, stamp(), { key: key, login: login, password: pw.value } )
			} ).then( function ( r ) {
				busy( form, false );
				if ( r.status >= 400 ) {
					msg( msgBox, 'err', ( r.json.data && r.json.data.message ) || 'That reset link is invalid or expired. Request a new one.' );
					return;
				}
				CFG.loggedIn = true;
				CFG.wpNonce = r.json.data && r.json.data.nonce || '';
				var to = ( r.json.data && r.json.data.redirect_to ) || CFG.accountUrl;
				if ( to && '/' === to.charAt( 0 ) ) {
					to = window.location.origin + to;
				}
				if ( to && to.indexOf( window.location.origin ) === 0 ) {
					window.location.href = to;
				}
			} ).catch( function () {
				busy( form, false );
				msg( msgBox, 'err', 'Network error. Try again.' );
			} );
		} );
	}

	/* ---------- ticket form ---------- */

	function mountTicket() {
		var root = el( 'div', { className: 'pdex' } );
		if ( ! authed() ) {
			root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'Submit a ticket' ) );
			var log = el( 'div', { className: 'pdex-panel' } );
			log.appendChild( el( 'p', { style: 'margin-bottom:1rem' }, 'Tickets (questions, evidence, corrections, help) are for Parent Data Force members — log in to continue.' ) );
			var go = el( 'a', {
				className: 'pdex-btn pdex-quiet',
				href: CFG.loginUrl + '?redirect_to=' + encodeURIComponent( CFG.ticketUrl ),
				style: 'text-decoration:none'
			}, 'Log in' );
			log.appendChild( go );
			log.appendChild( document.createTextNode( '  ·  ' ) );
			log.appendChild( el( 'a', { href: CFG.registerUrl, style: 'color:var(--wp--preset--color--accent-2)' }, 'Create an account' ) );
			root.appendChild( log );
			ROOT.appendChild( root );
			return;
		}

		// private-message notice above the form
		root.appendChild( el( 'p', { className: 'pdex-t-meta', style: 'margin:0 0 0.9rem' },
			'Tickets are private messages to Parent Data Force staff — only you and our team can read them. Pick what kind of message this is:' ) );

		var form = el( 'form', { novalidate: true } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
		var subject = el( 'input', { type: 'text', id: 'pdex-t-subject', required: true, maxLength: 150 } );
		var kind = 'question';
		var kindHidden = el( 'input', { type: 'hidden', value: kind, 'aria-hidden': 'true' } );

		// Category cards: plain-language labels; the stored value is the
		// kind string in the hidden input.
		var KINDS = [
			[ 'question', 'Ask a question', 'Something you want to know about district data, records, or a story you saw.' ],
			[ 'evidence', 'Share information or evidence', 'Documents, emails, test scores, or observations about a district.' ],
			[ 'help', 'Request help', 'You need help understanding or acting on something for your child or district.' ],
			[ 'correction', 'Report a correction', 'Something on this site is wrong or out of date.' ],
			[ 'other', 'Something else', 'Anything that does not fit the options above.' ]
		];
		var cards = el( 'div', { className: 'pdex-cards', role: 'radiogroup', 'aria-label': 'What kind of message is this?' } );
		KINDS.forEach( function ( k ) {
			var card = el( 'button', {
				type: 'button',
				className: 'pdex-card' + ( k[ 0 ] === kind ? ' on' : '' ),
				'data-kind': k[ 0 ]
			} );
			card.appendChild( el( 'span', { className: 'pdex-card-t', text: k[ 1 ] } ) );
			card.appendChild( el( 'span', { className: 'pdex-card-d', text: k[ 2 ] } ) );
			card.addEventListener( 'click', function () {
				kind = k[ 0 ];
				kindHidden.value = kind;
				var all = cards.querySelectorAll( '.pdex-card' );
				for ( var i = 0; i < all.length; i++ ) {
					all[ i ].classList.toggle( 'on', all[ i ] === card );
				}
			} );
			cards.appendChild( card );
		} );

		var district = el( 'input', { type: 'text', id: 'pdex-t-district', maxLength: 120 } );
		var dRow = el( 'div', { className: 'pdex-row' } );
		dRow.appendChild( el( 'label', { for: 'pdex-t-district' }, 'School district (optional)' ) );
		dRow.appendChild( district );

		var body = el( 'textarea', { id: 'pdex-t-body', required: true, placeholder: 'Tell us what happened, what you need, or what is wrong…' } );
		var counter = el( 'div', { className: 'pdex-t-meta', text: '' } );
		body.addEventListener( 'input', function () {
			counter.textContent = body.value.length + ' / 8000 characters';
		} );

		var sRow = el( 'div', { className: 'pdex-row' } );
		sRow.appendChild( el( 'label', { for: 'pdex-t-subject' }, 'Subject (150 chars)' ) );
		sRow.appendChild( subject );

		var bRow = el( 'div', { className: 'pdex-row' } );
		bRow.appendChild( el( 'label', { for: 'pdex-t-body' }, 'Your ticket' ) );
		bRow.appendChild( body );

		form.appendChild( kindHidden );
		form.appendChild( msgBox );
		form.appendChild( sRow );
		form.appendChild( cards );
		form.appendChild( dRow );
		form.appendChild( bRow );
		form.appendChild( counter );

		// honeypot, invisible
		var hp = el( 'div', { style: 'position:absolute;left:-9999px;top:-9999px', 'aria-hidden': 'true' } );
		hp.appendChild( el( 'input', { type: 'text', name: 'pdforce_website', tabIndex: '-1', autocomplete: 'off' } ) );
		form.appendChild( hp );

		form.appendChild( el( 'button', { type: 'submit' }, 'Submit ticket' ) );
		root.appendChild( form );
		ROOT.appendChild( root );

		form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( form, true );
			if ( body.value.trim().length < 20 ) {
				busy( form, false );
				msg( msgBox, 'err', 'Ticket body must be at least 20 characters.' );
				return;
			}
			var payload = stamp();
			payload.t_subject = subject.value;
			payload.t_kind = kind;
			payload.t_district = district.value;
			payload.t_body = body.value;
			api( '/pdforce/v1/ticket', { body: payload }, CFG.wpNonce ).then( function ( r ) {
				busy( form, false );
				if ( r.status >= 400 ) {
					msg( msgBox, 'err', ( r.json.data && r.json.data.message ) || 'Could not submit. Try again.' );
					return;
				}
				CFG.wpNonce = r.json.data && r.json.data.nonce || CFG.wpNonce;
				window.location.href = CFG.accountUrl + '#ticket-' + ( r.json.data && r.json.data.id );
			} ).catch( function () {
				busy( form, false );
				msg( msgBox, 'err', 'Network error. Try again.' );
			} );
		} );
	}

	/* ---------- account dashboard ---------- */

	function mountAccount() {
		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' }, authed() ? 'My account' : 'Members area' ) );

		if ( ! authed() ) {
			var box = el( 'div', { className: 'pdex-panel' } );
			box.appendChild( el( 'p', { style: 'margin-bottom:1rem' },
				'Create an account to comment on articles and submit tickets — questions, evidence, corrections and help with Massachusetts school-district data.' ) );
			var row = el( 'p', { style: 'margin:0' } );
			row.appendChild( el( 'a', { href: CFG.registerUrl, className: 'pdex-btn', style: 'text-decoration:none;display:inline-block' }, 'Create account' ) );
			row.appendChild( document.createTextNode( '  ' ) );
			row.appendChild( el( 'a', {
				href: CFG.loginUrl,
				className: 'pdex-btn pdex-quiet',
				style: 'text-decoration:none;display:inline-block'
			}, 'Log in' ) );
			box.appendChild( row );
			root.appendChild( box );
			ROOT.appendChild( root );
			return;
		}

		ROOT.appendChild( root );

		function failProfile() {
			root.appendChild( el( 'p', { className: 'pdex-t-meta' }, 'Could not load your profile — refresh the page.' ) );
		}

		api( '/pdforce/v1/profile', { method: 'GET' }, CFG.wpNonce ).then( function ( r ) {
			var p = r.json && r.json.data;
			if ( r.status >= 400 || ! p ) {
				failProfile();
				return;
			}
			if ( 0 === ( p.privacy_set | 0 ) ) {
				renderFirstRun( root, p );
				return;
			}
			renderDashboard( root, p );
		} ).catch( failProfile );
	}

	/** Shared profile form (first-run chooser and dashboard details). */
	function profileFields( p ) {
		var form = el( 'form', { novalidate: true } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );

		var nameRow = el( 'div', { className: 'pdex-row' } );
		nameRow.appendChild( el( 'label', { for: 'pdex-p-name' }, 'Display name' ) );
		nameRow.appendChild( el( 'input', { type: 'text', id: 'pdex-p-name', maxLength: 60, value: p.display_name || '' } ) );
		form.appendChild( nameRow );

		var roleRow = el( 'div', { className: 'pdex-row' } );
		roleRow.appendChild( el( 'label', { for: 'pdex-p-role' }, 'I am a…' ) );
		var roleSel = el( 'select', { id: 'pdex-p-role' } );
		[ '', 'parent', 'educator', 'advocate', 'other' ].forEach( function ( rr ) {
			roleSel.appendChild( el( 'option', { value: rr },
				'' === rr ? 'Prefer not to say' : rr.charAt( 0 ).toUpperCase() + rr.slice( 1 ) ) );
		} );
		roleSel.value = p.role || '';
		roleRow.appendChild( roleSel );
		form.appendChild( roleRow );

		var dRow = el( 'div', { className: 'pdex-row' } );
		dRow.appendChild( el( 'label', { for: 'pdex-p-district' }, 'School district (private — helps route your question)' ) );
		dRow.appendChild( el( 'input', { type: 'text', id: 'pdex-p-district', maxLength: 120, value: p.district || '' } ) );
		form.appendChild( dRow );

		[
			[ 'show_name', 'Show my name on public comments' ],
			[ 'show_role', 'Show my role on public comments' ],
			[ 'show_district', 'Show my district on public comments' ]
		].forEach( function ( ck ) {
			var row = el( 'div', { className: 'pdex-check' } );
			var cb = el( 'input', { type: 'checkbox', id: 'pdex-' + ck[ 0 ] } );
			cb.checked = !! p[ ck[ 0 ] ];
			row.appendChild( cb );
			row.appendChild( el( 'label', { for: 'pdex-' + ck[ 0 ] }, ck[ 1 ] ) );
			form.appendChild( row );
		} );

		form.appendChild( msgBox );
		return { form: form, msgBox: msgBox, nameRow: nameRow, roleSel: roleSel, dRow: dRow };
	}

	function profilePayload( nodes ) {
		return Object.assign( {}, stamp(), {
			display_name: nodes.nameRow.querySelector( 'input' ).value,
			pdforce_role: nodes.roleSel.value,
			pdforce_district: nodes.dRow.querySelector( 'input' ).value,
			show_name: nodes.form.querySelector( '#pdex-show_name' ).checked ? 1 : 0,
			show_role: nodes.form.querySelector( '#pdex-show_role' ).checked ? 1 : 0,
			show_district: nodes.form.querySelector( '#pdex-show_district' ).checked ? 1 : 0
		} );
	}

	function postProfile( nodes, done, fail ) {
		api( '/pdforce/v1/profile', { body: profilePayload( nodes ) }, CFG.wpNonce )
			.then( function ( r ) {
				if ( r.status >= 400 ) {
					fail( ( r.json.data && r.json.data.message ) || 'Could not save. Try again.' );
					return;
				}
				done( r.json.data || {} );
			} )
			.catch( function () {
				fail( 'Network error. Try again.' );
			} );
	}

	/** Dashboard: hello, tickets, log out, Profile & privacy details. */
	function renderDashboard( root, p ) {
		var hello = el( 'p', { className: 'pdex-t-meta', id: 'pdex-hello' }, '' );
		root.appendChild( hello );

		var head = el( 'h2', { style: 'font-size:1.3rem;margin:1.6rem 0 .5rem' }, 'Your tickets' );
		var hint = el( 'p', { className: 'pdex-t-meta' }, 'Questions, evidence, corrections and help requests you sent. Status changes are posted here and emailed.' );
		var list = el( 'ul', { className: 'pdex-tickets', id: 'pdex-tickets' } );
		root.appendChild( head );
		root.appendChild( hint );
		root.appendChild( list );

		var newBtn = el( 'div', { className: 'pdex-row', style: 'margin-top:1.2rem' } );
		newBtn.appendChild( el( 'a', {
			href: CFG.ticketUrl,
			className: 'pdex-btn',
			style: 'text-decoration:none'
		}, 'Submit a new ticket' ) );
		root.appendChild( newBtn );

		var out = el( 'div', { className: 'pdex-row', style: 'margin-top:1.4rem' } );
		out.appendChild( el( 'button', {
			className: 'pdex-quiet',
			onClick: function () {
				api( '/pdforce/v1/logout', {}, CFG.wpNonce ).then( function () {
					window.location.reload();
				} ).catch( function () {
					window.location.href = CFG.accountUrl;
				} );
			}
		}, 'Log out' ) );
		root.appendChild( out );

		// Profile & privacy, prefilled; saved in place.
		var det = el( 'details', { className: 'pdex-profile' } );
		det.appendChild( el( 'summary', null, 'Profile & privacy' ) );
		var nodes = profileFields( p );
		nodes.form.appendChild( el( 'button', { type: 'submit' }, 'Save' ) );
		det.appendChild( nodes.form );
		nodes.form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( nodes.form, true );
			postProfile( nodes, function () {
				busy( nodes.form, false );
				msg( nodes.msgBox, 'ok', 'Profile saved.' );
			}, function ( t ) {
				busy( nodes.form, false );
				msg( nodes.msgBox, 'err', t );
			} );
		} );
		root.appendChild( det );

		// hello + tickets
		api( '/wp/v2/users/me', { method: 'GET' }, CFG.wpNonce ).then( function ( r ) {
			if ( r.status < 400 && r.json && r.json.name ) {
				root.removeChild( hello );
				hello = el( 'p', { className: 'pdex-t-meta' }, 'Logged in as ' + r.json.name + '.' );
				root.insertBefore( hello, head );
			}
		} ).catch( function () {} );

		api( '/pdforce/v1/tickets/mine', { method: 'GET' }, CFG.wpNonce ).then( function ( r ) {
			var src = ( r.json && r.json.data && r.json.data.tickets ) || [];
			if ( ! src.length ) {
				list.appendChild( el( 'li', { className: 'pdex-ticket' }, 'No tickets yet.' ) );
				return;
			}
			src.forEach( function ( t ) {
				list.appendChild( ticketCard( t ) );
			} );
		} ).catch( function () {
			list.appendChild( el( 'li', { className: 'pdex-ticket' }, 'Could not load your tickets — refresh the page.' ) );
		} );

		openFromHash();
	}

	/** First-run privacy chooser shown instead of the dashboard. */
	function renderFirstRun( root, p ) {
		root.appendChild( el( 'h2', { style: 'font-size:1.4rem;margin:0.7rem 0 0.4rem' },
			'How do you want to appear when you comment publicly?' ) );
		root.appendChild( el( 'p', { className: 'pdex-t-meta', style: 'margin:0 0 1.1rem' },
			'Your first comment is reviewed before it appears. You can change this anytime.' ) );
		var nodes = profileFields( p );
		nodes.form.appendChild( el( 'button', { type: 'submit' }, 'Continue' ) );
		root.appendChild( nodes.form );
		nodes.form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( nodes.form, true );
			postProfile( nodes, function () {
				window.location.reload();
			}, function ( t ) {
				busy( nodes.form, false );
				msg( nodes.msgBox, 'err', t );
			} );
		} );
	}

	function ticketCard( t ) {
		var card = el( 'li', { className: 'pdex-ticket', id: 'ticket-' + t.id } );
		var det = el( 'details' );
		var sum = el( 'summary' );
		sum.appendChild( el( 'span', { text: t.subject } ) );
		var meta = el( 'div', { className: 'pdex-t-meta',
			text: t.kind + ' · ' + fmtDate( t.date ) + ( t.district ? ' · ' + t.district : '' ) } );
		sum.appendChild( meta );
		sum.appendChild( el( 'span', { className: 'pdex-t-status', 'data-status': t.status, text: t.status } ) );
		det.appendChild( sum );

		var thread = el( 'div', { className: 'pdex-t-thread' } );
		det.appendChild( thread );
		det.addEventListener( 'toggle', function () {
			if ( det.open && ! det.dataset.loaded ) {
				det.dataset.loaded = '1';
				loadThread( t, thread );
			}
		} );
		card.appendChild( det );
		return card;
	}

	function loadThread( t, thread ) {
		api( '/pdforce/v1/tickets/' + t.id, { method: 'GET' }, CFG.wpNonce ).then( function ( r ) {
			if ( r.status >= 400 || ! ( r.json && r.json.data ) ) {
				thread.appendChild( el( 'p', { className: 'pdex-t-meta', text: 'Could not load the thread.' } ) );
				return;
			}
			var data = r.json.data;
			// body
			var opening = el( 'div', { className: 'pdex-t-msg' } );
			opening.appendChild( el( 'div', { className: 'pdex-t-msg by', text: 'Original message — ' + fmtDate( data.ticket.date ) } ) );
			var bodyDoc = el( 'div' );
			// body is wpautop'd sanitized text; strip to plain for safety
			bodyDoc.textContent = data.ticket.body.replace( /<[^>]*>/g, ' ' );
			opening.appendChild( bodyDoc );
			thread.appendChild( opening );

			( data.comments || [] ).forEach( function ( c ) {
				var row = el( 'div', { className: 'pdex-t-msg' + ( c.is_owner ? ' is-owner' : '' ) } );
				row.appendChild( el( 'div', { className: 'pdex-t-msg by', text: c.author + ' — ' + fmtDate( c.date ) } ) );
				var cd = el( 'div' );
				cd.textContent = ( c.content || '' ).replace( /<[^>]*>/g, ' ' ).trim();
				row.appendChild( cd );
				thread.appendChild( row );
			} );

			// reply box
			var reply = el( 'div', { className: 'pdex-row pdex-reply' } );
			var ta = el( 'textarea', { placeholder: 'Add to the conversation…' } );
			reply.appendChild( ta );
			var send = el( 'button', {
				className: 'pdex-quiet',
				onClick: function () {
					if ( ta.value.trim().length < 2 ) {
						return;
					}
					send.disabled = true;
					api( '/pdforce/v1/tickets/' + t.id + '/reply', {
						method: 'POST',
						body: { body: ta.value }
					}, CFG.wpNonce ).then( function ( r ) {
						send.disabled = false;
						if ( r.status >= 400 ) {
							return;
						}
						ta.value = '';
						while ( thread.firstChild ) {
							thread.removeChild( thread.firstChild );
						}
						loadThread( t, thread );
					} );
				}
			}, 'Reply' );
			reply.appendChild( send );
			thread.appendChild( reply );
		} ).catch( function () {
			thread.appendChild( el( 'p', { className: 'pdex-t-meta', text: 'Could not load the thread.' } ) );
		} );
	}

	function openFromHash() {
		var m = ( window.location.hash || '' ).match( /^#ticket-(\d+)$/ );
		if ( ! m ) {
			return;
		}
		var target = document.getElementById( 'ticket-' + m[ 1 ] );
		if ( target ) {
			var d = target.querySelector( 'details' );
			if ( d ) {
				d.open = true;
			}
			target.scrollIntoView( { block: 'start' } );
		}
	}

	/* ---------- boot ---------- */

	function boot() {
		headerBadge();
		if ( authed() && ( 'register' === CFG.page || 'login' === CFG.page ) ) {
			// Already signed in: auth pages have nothing to offer.
			window.location.replace( CFG.accountUrl );
			return;
		}
		switch ( CFG.page ) {
			case 'register': mountForm( 'register' ); break;
			case 'login': mountForm( 'login' ); break;
			case 'ticket': mountTicket(); break;
			case 'account': mountAccount(); break;
			case 'confirm': mountConfirm(); break;
			case 'reset': mountReset(); break;
			default: mountCommentsHint(); break;
		}
	}

	if ( 'loading' === document.readyState ) {
		document.addEventListener( 'DOMContentLoaded', boot );
	} else {
		boot();
	}
} )();
