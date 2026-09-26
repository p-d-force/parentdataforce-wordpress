/**
 * Parent Data Force — member account front-end.
 *
 * Vanilla JS, no dependencies. Mounts into whatever #pdforce-account-root
 * exists on one of the four account pages (body class is_page-account /
 * -register / -login / -ticket set by the mu-plugin) and drives comment
 * gating hints on single posts.
 *
 * All state comes from pdforceAccount (wp_localize_script by the
 * pdforce-account mu-plugin): page, restUrl, loggedIn, wpNonce,
 * accountUrl, registerUrl, loginUrl, ticketUrl.
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
					} else if ( k.indexOf( 'data-' ) === 0 ) {
						n.setAttribute( k, attrs[ k ] );
					} else if ( k.indexOf( 'on' ) === 0 ) {
						n.addEventListener( k.slice( 2 ), attrs[ k ] );
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
		if ( 'post' !== CFG.page && authed() ) {
			var form = document.querySelector( '.wp-block-post-comments-form' );
			if ( form ) {
				return; // logged in -> core form stands on its own
			}
			var why = el( 'div', { id: 'pdforce-comment-gate',
				style: 'max-width:750px;margin:2rem auto;padding:1rem 1.25rem;'
					+ 'border:1px solid #1d1d1d;border-radius:10px;background:#161616;'
					+ 'font-size:.92rem;' } );
			why.appendChild( el( 'p', {
				className: 'pdex-kicker',
				style: 'margin-bottom:.5rem'
			}, 'Join the conversation' ) );
			why.appendChild( el( 'p', {
				style: 'margin:0'
			}, 'Comments are open to Parent Data Force members. Create an account (it takes a minute; your first comment is reviewed, the rest post instantly).' ) );
			var row = el( 'p', { style: 'margin:.9rem 0 0' } );
			row.appendChild( el( 'a', {
				href: CFG.registerUrl,
				className: 'pdex-btn',
				style: 'text-decoration:none'
			}, 'Create account' ) );
			row.appendChild( document.createTextNode( '  ' ) );
			row.appendChild( el( 'a', {
				className: 'pdex-quiet pdex-btn',
				href: CFG.loginUrl,
				style: 'text-decoration:none'
			}, 'Log in' ) );
			why.appendChild( row );
			form.appendChild( why );
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
		ROOT.appendChild( root );

		form.addEventListener( 'submit', function ( ev ) {
			ev.preventDefault();
			busy( form, true );
			msg( msgBox, '', '' );

			var payload = stamp();
			payload.redirect_to = CFG.accountUrl;
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
					showMsg( null, msgBox, ( res.json.data && res.json.data.message ) || 'That did not work. Try again.' );
					return;
				}
				CFG.loggedIn = true;
				CFG.wpNonce = res.json.data && res.json.data.nonce || '';
				var to = ( res.json.data && res.json.data.redirect_to ) || CFG.accountUrl;
				if ( to && to.indexOf( window.location.origin ) === 0 ) {
					window.location.href = to;
				}
			} ).catch( function () {
				busy( form, false );
				showMsg( null, msgBox, 'Network error. Try again.' );
			} );
		} );
	}

	/* ---------- ticket form ---------- */

	function mountTicket() {
		var root = el( 'div', { className: 'pdex' } );
		if ( ! authed() ) {
			root.appendChild( el( 'p', { className: 'pdex-kicker' }, 'Submit a ticket' ) );
			var log = el( 'div', { className: 'pdex-panel' } );
			log.appendChild( el( 'p', { style: 'margin-bottom:1rem' }, 'Tickets (data requests, corrections, questions) are for Parent Data Force members — log in to continue.' ) );
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

		var form = el( 'form', { novalidate: true } );
		var msgBox = el( 'div', { className: 'pdex-msg', 'aria-live': 'polite' } );
		var subject = el( 'input', { type: 'text', id: 'pdex-t-subject', required: true, maxLength: 150 } );
		var kind;
		var kindWrap = el( 'div', { className: 'pdex-row-split' } );

		function half( name, label, node ) {
			var w = el( 'div' );
			w.appendChild( el( 'label', { for: name }, label ) );
			w.appendChild( node );
			return w;
		}
		kind = el( 'select', { id: 'pdex-t-kind' } );
		[ 'question', 'data', 'correction', 'other' ].forEach( function ( k ) {
			kind.appendChild( el( 'option', { value: k }, k.charAt( 0 ).toUpperCase() + k.slice( 1 ) ) );
		} );
		var district = el( 'input', { type: 'text', id: 'pdex-t-district', maxLength: 120 } );
		kindWrap.appendChild( half( 'pdex-t-kind', 'Type', kind ) );
		kindWrap.appendChild( half( 'pdex-t-district', 'School district (optional)', district ) );

		var body = el( 'textarea', { id: 'pdex-t-body', required: true, placeholder: 'What do you need? Data, corrections, questions…' } );
		var counter = el( 'div', { className: 'pdex-t-meta', text: '' } );
		body.addEventListener( 'input', function () {
			counter.textContent = body.value.length + ' / 8000 characters';
		} );

		form.appendChild( msgBox );
		form.appendChild( half( 'pdex-t-subject', 'Subject (150 chars)', subject ) );
		form.appendChild( kindWrap );
		form.appendChild( half( 'pdex-t-body', 'Your ticket', body ) );
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
			payload.t_kind = kind.value;
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

	var STATUS_PAGES = { login: mountForm, register: mountForm };

	function mountAccount() {
		var root = el( 'div', { className: 'pdex' } );
		root.appendChild( el( 'p', { className: 'pdex-kicker' }, authed() ? 'My account' : 'Members area' ) );

		if ( ! authed() ) {
			var box = el( 'div', { className: 'pdex-panel' } );
			box.appendChild( el( 'p', { style: 'margin-bottom:1rem' },
				'Create an account to comment on articles and submit tickets — data requests, corrections, questions about Massachusetts school-district data.' ) );
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

		var hello = el( 'p', { className: 'pdex-t-meta', id: 'pdex-hello' }, '' );
		root.appendChild( hello );

		var head = el( 'h2', { style: 'font-size:1.3rem;margin:1.6rem 0 .5rem' }, 'Your tickets' );
		var hint = el( 'p', { className: 'pdex-t-meta' }, 'Data requests, corrections, questions you sent. Status changes are posted here and emailed.' );
		var list = el( 'ul', { className: 'pdex-tickets', id: 'pdex-tickets' } );
		root.appendChild( head );
		root.appendChild( hint );
		root.appendChild( list );

		var newBtn = el( 'div', { className: 'pdex-row', style: 'margin-top:1.2rem' } );
		var b = el( 'a', {
			href: CFG.ticketUrl,
			className: 'pdex-btn',
			style: 'text-decoration:none'
		}, 'Submit a new ticket' );
		newBtn.appendChild( b );
		root.appendChild( newBtn );

		var out = el( 'div', { className: 'pdex-row', style: 'margin-top:1.4rem' } );
		var lo = el( 'button', {
			className: 'pdex-quiet',
			onClick: function () {
				api( '/pdforce/v1/logout', {}, CFG.wpNonce ).then( function () {
					window.location.reload();
				} ).catch( function () {
					window.location.href = CFG.accountUrl;
				} );
			}
		}, 'Log out' );
		out.appendChild( lo );
		root.appendChild( out );

		ROOT.appendChild( root );

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
						det.dataset.loaded = '';
						det.open = true;
						det.dispatchEvent( new Event( 'toggle' ) );
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
		switch ( CFG.page ) {
			case 'register': mountForm( 'register' ); break;
			case 'login': mountForm( 'login' ); break;
			case 'ticket': mountTicket(); break;
			case 'account': mountAccount(); break;
			default: mountCommentsHint(); break;
		}
	}

	if ( 'loading' === document.readyState ) {
		document.addEventListener( 'DOMContentLoaded', boot );
	} else {
		boot();
	}
} )();
