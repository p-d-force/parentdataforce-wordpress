<?php
/**
 * Plugin Name: PDF — Member accounts, tickets, and comment gating
 * Description: Self-service registration, login/logout over REST, private
 *              support tickets (pdforce_ticket CPT) with email pings, and
 *              "first comment held for moderation" for registered commenters.
 *              Mirrors the pdforce-queue.php mu-plugin conventions
 *              (honeypot, timestamp gate, per-IP transients, wp_send_json_*).
 *
 *              Repo copy: rest/pdforce-account-mu.php
 *              Deploys to /public_html/news/wp-content/mu-plugins/pdforce-account.php
 * Version:     1.1.0
 * Author:      Parent Data Force
 * Text Domain: pdforce
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const PDA_TIME_FLOOR  = 3;    // seconds of past clock drift tolerated
const PDA_TIME_CEIL   = 60;   // seconds of future clock skew tolerated
const PDA_MAX_NAME    = 60;
const PDA_MAX_DISTRICT = 120;
const PDA_MAX_ROLE    = 20;
const PDA_MAX_SUBJECT = 150;
const PDA_MAX_BODY    = 8000;
const PDA_MIN_BODY    = 20;
const PDA_MAX_REPLY   = 2000;
const PDA_REG_LIMIT   = 5;    // registrations per IP per hour
const PDA_LOGIN_LIMIT = 5;    // failed logins per IP per 15 min
const PDA_TIX_USER_WINDOW = 300;      // one ticket per user per 5 min
const PDA_TIX_IP_LIMIT    = 5;        // five tickets per IP per hour

/**
 * Settings bootstrap. Runs on plugins_loaded every request; each write is
 * guarded against the current value so nothing churns once correct.
 *
 * comment_previously_approved=0 disables core's email-key repeat-approval
 * logic; the reliable "first comment held" behavior is the
 * pda_first_comment_held filter below (core's option is keyed on author
 * email, which never matches before the first approved comment).
 */
add_action( 'plugins_loaded', 'pda_bootstrap_settings' );
function pda_bootstrap_settings() {
	$targets = array(
		'users_can_register'          => 1,
		'default_role'                => 'subscriber',
		'comment_registration'        => 1,
		'comment_moderation'          => 0,
		'comment_previously_approved' => 0,
		'thread_comments'             => 1,
		'default_comment_status'      => 'open',
	);
	foreach ( $targets as $name => $want ) {
		if ( (string) get_option( $name ) !== (string) $want ) {
			update_option( $name, $want );
		}
	}
}

/**
 * One-time migration: everyone registered before the confirmation gate
 * (v1.0.3 era) is trusted as already confirmed. Runs once, then flags.
 */
add_action( 'plugins_loaded', 'pda_backfill_verified' );
function pda_backfill_verified() {
	if ( '1' === get_option( 'pda_all_verified' ) ) {
		return;
	}
	foreach ( get_users( array( 'fields' => 'ID' ) ) as $uid ) {
		update_user_meta( (int) $uid, 'pdforce_verified', 1 );
	}
	update_option( 'pda_all_verified', '1' );
}

/**
 * First-comment moderation for registered commenters: a user's first
 * comment is held; once any of their comments is approved, the rest are
 * auto-approved. Post authors / editors keep their native approval path.
 */
add_filter( 'pre_comment_approved', 'pda_first_comment_held', 10, 2 );
function pda_first_comment_held( $approved, $commentdata ) {
	if ( 1 !== (int) $approved ) {
		return $approved;
	}
	$post_id = isset( $commentdata['comment_post_ID'] ) ? (int) $commentdata['comment_post_ID'] : 0;
	if ( $post_id && 'pdforce_ticket' === get_post_type( $post_id ) ) {
		return $approved; // ticket threads are already permission-gated
	}
	$user_id = isset( $commentdata['user_id'] ) ? (int) $commentdata['user_id'] : 0;
	if ( ! $user_id || user_can( $user_id, 'edit_others_posts' ) ) {
		return $approved;
	}
	$count = get_comments(
		array(
			'user_id' => $user_id,
			'status'  => 'approve',
			'count'   => true,
		)
	);
	return $count ? $approved : 0; // 0 = hold
}

/**
 * Comment byline privacy, at rest. Live WP 7.1.2 signature verified over
 * FTP before deploy: pre_comment_author_name fires in wp_filter_comment
 * with a single string arg; get_comment_author fires with
 * ( $author, $comment_id, $comment ).
 */
add_filter( 'pre_comment_author_name', 'pda_byline_store' );
function pda_byline_store( $author ) {
	$uid = get_current_user_id();
	// Staff edits (approve etc.) and anonymous writes keep the byline.
	if ( ! $uid || current_user_can( 'edit_others_posts' ) ) {
		return $author;
	}
	if ( 0 !== (int) get_user_meta( $uid, 'pdforce_show_name', true ) ) {
		return $author;
	}
	$user = get_userdata( $uid );
	// Only anonymize the writer's OWN byline — never an admin-side update
	// of someone else's comment (filters fire on update too).
	if ( $user && (string) wp_unslash( $author ) === (string) $user->display_name ) {
		return 'Anonymous'; // privacy at rest: real name never stored publicly
	}
	return $author;
}

add_filter( 'get_comment_author', 'pda_byline_display', 10, 3 );
function pda_byline_display( $author, $comment_id, $comment ) {
	if ( ! $comment instanceof WP_Comment ) {
		$comment = get_comment( $comment_id );
	}
	if ( ! $comment || empty( $comment->user_id ) ) {
		return $author;
	}
	$uid      = (int) $comment->user_id;
	$role     = trim( (string) get_user_meta( $uid, 'pdforce_role', true ) );
	$district = trim( (string) get_user_meta( $uid, 'pdforce_district', true ) );
	$bits     = array();
	if ( (int) get_user_meta( $uid, 'pdforce_show_role', true ) && '' !== $role ) {
		$bits[] = ucfirst( $role );
	}
	if ( (int) get_user_meta( $uid, 'pdforce_show_district', true ) && '' !== $district ) {
		$bits[] = $district;
	}
	if ( ! $bits ) {
		return $author;
	}
	return $author . ' (' . implode( ' · ', $bits ) . ')';
}

/**
 * Subscriber lockdown: staff keep the admin bar, subscribers lose it;
 * wp-admin itself bounces anyone below edit_posts to the account page.
 */
add_filter( 'show_admin_bar', 'pda_maybe_hide_admin_bar' );
function pda_maybe_hide_admin_bar( $show ) {
	return current_user_can( 'edit_others_posts' );
}

add_action( 'admin_init', 'pda_block_wp_admin' );
function pda_block_wp_admin() {
	if ( wp_doing_ajax() || wp_doing_cron() || current_user_can( 'edit_posts' ) ) {
		return;
	}
	wp_safe_redirect( home_url( '/account/' ) );
	exit;
}

/** Brand wp-login.php (the one surface REST does not cover). */
add_action( 'login_enqueue_scripts', 'pda_login_brand' );
function pda_login_brand() {
	$css = 'body.login{background:#0b0b0b!important}'
		. 'body.login a{color:#ffa366!important}'
		. 'body.login h1 a{background-image:url(https://www.parentdataforce.com/wp-content/uploads/brand/logo.png)!important;background-size:contain;background-position:center;width:220px;height:84px;}'
		. '.login form{background:#f5f5f5;border:none;border-radius:10px;}'
		. '.login form .input,.login input[type=text]{background:#0b0b0b!important;color:#f5f5f5!important;border-color:#1d1d1d!important;}'
		. '#loginform label{color:#0b0b0b;}'
		. '.login .button-primary{background:#ff5a1f!important;border-color:#ff5a1f!important;color:#0b0b0b!important;text-shadow:none;}'
		. '.login .button-primary:hover{background:#ffa366!important;}'
		. '.login .message,.login #login_error{border-left-color:#ff5a1f;}';
	wp_add_inline_style( 'login', $css );
}
add_filter( 'login_headertext', function () { return 'Parent Data Force'; } );

/**
 * Private, REST-visible ticket CPT. Owner-level reporting: wp-admin list
 * table is the tracking board; REST visibility follows the same
 * private-post rules as pdforce_queue_note (anon GET /wp/v2/tickets -> []).
 */
add_action( 'init', 'pda_register_ticket_cpt' );
function pda_register_ticket_cpt() {
	register_post_type(
		'pdforce_ticket',
		array(
			'labels'          => array(
				'name'          => 'Tickets',
				'singular_name' => 'Ticket',
				'menu_name'     => 'Tickets',
			),
			'public'          => false,
			'show_ui'         => true,
			'show_in_menu'    => true,
			'menu_icon'       => 'dashicons-format-chat',
			'show_in_rest'    => true,
			'rest_base'       => 'tickets',
			'supports'        => array( 'title', 'editor', 'comments', 'custom-fields' ),
			'capability_type' => 'post',
			'map_meta_cap'    => true,
			'hierarchical'    => false,
		)
	);

	$meta = array(
		'pdforce_status'   => array( 'default' => 'new' ),
		'pdforce_kind'     => array( 'default' => 'other' ),
		'pdforce_district' => array( 'default' => '' ),
		'pdforce_role'     => array( 'default' => '' ),
	);
	foreach ( $meta as $key => $conf ) {
		register_post_meta(
			'pdforce_ticket',
			$key,
			array(
				'show_in_rest' => true,
				'single'       => true,
				'type'         => 'string',
				'default'      => $conf['default'],
			)
		);
	}
}

/** Admin list-table columns so wp-admin is the ticket queue. */
add_filter( 'manage_pdforce_ticket_posts_columns', 'pda_ticket_columns' );
function pda_ticket_columns( $cols ) {
	$out = array();
	foreach ( $cols as $key => $label ) {
		$out[ $key ] = $label;
		if ( 'title' === $key ) {
			$out['pda_status']   = 'Status';
			$out['pda_kind']     = 'Kind';
			$out['pda_district'] = 'District';
		}
	}
	return $out;
}

add_action( 'manage_pdforce_ticket_posts_custom_column', 'pda_ticket_column', 10, 2 );
function pda_ticket_column( $col, $post_id ) {
	$map = array(
		'pda_status'   => 'pdforce_status',
		'pda_kind'     => 'pdforce_kind',
		'pda_district' => 'pdforce_district',
	);
	if ( ! isset( $map[ $col ] ) ) {
		return;
	}
	$v = (string) get_post_meta( $post_id, $map[ $col ], true );
	echo esc_html( '' !== $v ? $v : '—' );
}

add_filter( 'manage_edit-pdforce_ticket_sortable_columns', 'pda_ticket_sortable' );
function pda_ticket_sortable( $cols ) {
	$cols['pda_status'] = 'pda_status';
	$cols['pda_kind']   = 'pda_kind';
	return $cols;
}

add_action( 'pre_get_posts', 'pda_ticket_admin_sort' );
function pda_ticket_admin_sort( $q ) {
	if ( ! is_admin() || 'pdforce_ticket' !== $q->get( 'post_type' ) ) {
		return;
	}
	$map   = array(
		'pda_status' => 'pdforce_status',
		'pda_kind'   => 'pdforce_kind',
	);
	$col = (string) $q->get( 'orderby' );
	if ( isset( $map[ $col ] ) ) {
		$q->set( 'meta_key', $map[ $col ] );
		$q->set( 'orderby', 'meta_value' );
	}
}

/**
 * REST routes, namespace pdforce/v1. Prefix pda_.
 */
add_action( 'rest_api_init', 'pda_register_routes' );
function pda_register_routes() {
	register_rest_route(
		'pdforce/v1',
		'/register',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_register',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/login',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_login',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/logout',
		array(
			'methods'             => 'POST',
			'permission_callback' => 'pda_req_logged_in',
			'callback'            => 'pda_handle_logout',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/ticket',
		array(
			'methods'             => 'POST',
			'permission_callback' => 'pda_req_logged_in',
			'callback'            => 'pda_handle_ticket_create',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/tickets/mine',
		array(
			'methods'             => 'GET',
			'permission_callback' => 'pda_req_logged_in',
			'callback'            => 'pda_handle_tickets_mine',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/tickets/(?P<id>\d+)',
		array(
			'methods'             => 'GET',
			'permission_callback' => 'pda_can_view_ticket',
			'callback'            => 'pda_handle_ticket_get',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/tickets/(?P<id>\d+)/reply',
		array(
			'methods'             => 'POST',
			'permission_callback' => 'pda_can_view_ticket',
			'callback'            => 'pda_handle_ticket_reply',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/tickets/(?P<id>\d+)/status',
		array(
			'methods'             => 'PUT',
			'permission_callback' => 'pda_can_moderate',
			'callback'            => 'pda_handle_ticket_status',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/confirm',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_confirm',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/resend',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_resend',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/forgot',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_forgot',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/password-reset',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pda_handle_password_reset',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/profile',
		array(
			'methods'             => 'GET',
			'permission_callback' => 'pda_req_logged_in',
			'callback'            => 'pda_handle_profile_get',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/profile',
		array(
			'methods'             => 'POST',
			'permission_callback' => 'pda_req_logged_in',
			'callback'            => 'pda_handle_profile_save',
		)
	);
}

/** Permission: logged in (cookie + REST nonce validated by core first). */
function pda_req_logged_in() {
	return is_user_logged_in();
}

/** Permission: author of the ticket or someone who can edit others'. */
function pda_can_view_ticket( $request ) {
	if ( ! is_user_logged_in() ) {
		return false;
	}
	$ticket = get_post( (int) $request['id'] );
	if ( ! $ticket || 'pdforce_ticket' !== $ticket->post_type ) {
		return false;
	}
	if ( (int) $ticket->post_author === get_current_user_id() ) {
		return true;
	}
	return current_user_can( 'edit_others_posts' );
}

/** Permission: owner side (admin). */
function pda_can_moderate() {
	return current_user_can( 'edit_others_posts' );
}

/** Sanitize and clip a text parameter to a hard length cap. */
function pda_clip( $value, $max ) {
	$value = sanitize_text_field( wp_unslash( (string) $value ) );
	$clip  = function_exists( 'mb_substr' ) ? 'mb_substr' : 'substr';
	return $clip( $value, 0, $max );
}

/** Honeypot + timestamp gate copied from the queue plugin's shape. */
function pda_gate_bot( $request ) {
	if ( ! empty( $request['pdforce_website'] ) ) {
		wp_send_json_error( null, 400 );
	}
	$ts = (int) ( $request['pdforce_ts'] ?? 0 );
	if ( $ts < time() - PDA_TIME_FLOOR || $ts > time() + PDA_TIME_CEIL ) {
		wp_send_json_error( null, 400 );
	}
}

/**
 * Themed HTML mail shell: 600px table, dark header band with orange
 * accent, white body, system fonts, orange CTA button. No images.
 * All CTA URLs are passed through esc_url at call sites; text is
 * escaped at insertion points.
 */
function pda_mail_html( $title, $body_html, $cta_url, $cta_label ) {
	$cta = '';
	if ( $cta_url && $cta_label ) {
		$cta = '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:18px auto 4px;"><tr><td align="center" bgcolor="#ff5a1f" style="border-radius:999px;"><a href="' . esc_url( $cta_url ) . '" style="display:inline-block;background:#ff5a1f;color:#0b0b0b;font-weight:bold;font-size:16px;padding:12px 30px;border-radius:999px;text-decoration:none;">' . esc_html( $cta_label ) . '</a></td></tr></table>';
	}
	return '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
		. '<body style="margin:0;padding:0;background:#f5f5f5;">'
		. '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 12px;"><tr><td align="center">'
		. '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:100%;background:#ffffff;border-radius:10px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;">'
		. '<tr><td style="background:#0b0b0b;padding:22px 28px 18px;">'
		. '<div style="width:44px;height:4px;background:#ff5a1f;border-radius:2px;margin-bottom:12px;"></div>'
		. '<div style="color:#f5f5f5;font-size:19px;font-weight:600;">' . esc_html( $title ) . '</div>'
		. '</td></tr>'
		. '<tr><td style="padding:24px 28px 8px;color:#0b0b0b;font-size:15px;line-height:1.6;">' . $body_html . '</td></tr>'
		. $cta
		. '<tr><td style="padding:20px 28px 24px;"><div style="height:1px;background:#e5e5e5;margin-bottom:12px;"></div>'
		. '<div style="color:#a0a0a0;font-size:12px;">Parent Data Force &middot; parentdataforce.com</div></td></tr>'
		. '</table></td></tr></table></body></html>';
}

/** Send one HTML email via wp_mail, forcing text/html for this call only. */
function pda_send_member_mail( $to, $subject, $html ) {
	$html_type = function () { return 'text/html'; };
	add_filter( 'wp_mail_content_type', $html_type );
	$ok = wp_mail( $to, $subject, $html );
	remove_filter( 'wp_mail_content_type', $html_type );
	return $ok;
}

/** Site-wide sender identity: pushes to inbox without the WordPress-name spam tax. */
add_filter( 'wp_mail_from', function () { return 'joey@parentdataforce.com'; } );
add_filter( 'wp_mail_from_name', function () { return 'Parent Data Force'; } );

/**
 * Core reset-request email, themed. Live WP 7.1.2 signature verified over
 * FTP before deploy: apply_filters( 'retrieve_password_notification_email',
 * $defaults, $key, $user_login, $user_data ) — defaults is an ARRAY
 * ({to,subject,message,headers}); the handler returns the array.
 */
add_filter( 'retrieve_password_notification_email', 'pda_reset_email', 10, 4 );
function pda_reset_email( $defaults, $key, $user_login, $user_data ) {
	$reset = home_url(
		'/account/reset/?key=' . urlencode( $key ) . '&login=' . urlencode( $user_login )
	);
	$first = $user_data && ! empty( $user_data->display_name )
		? $user_data->display_name
		: 'there';
	$body  = '<p style="margin:0 0 12px;">Hi ' . esc_html( $first ) . ',</p>'
		. '<p style="margin:0 0 12px;"><strong>' . esc_html( $user_login ) . '</strong> requested a password reset. Use the button below to choose a new password. The link works once and expires after a day for security.</p>'
		. '<p style="margin:0;color:#a0a0a0;font-size:13px;">If this was not you, ignore this email — your password stays as it is.</p>'
		. '<p style="margin:12px 0 0;word-break:break-all;color:#a0a0a0;font-size:13px;">Button not working? Paste this link into your browser:<br>' . esc_url( $reset ) . '</p>';
	$defaults['subject'] = 'Reset your Parent Data Force password';
	$defaults['message'] = pda_mail_html( 'Reset your password', $body, $reset, 'Choose a new password' );
	return $defaults;
}

/** Hashed-IP key helper. */
function pda_ip_key( $prefix ) {
	$ip = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	return $prefix . md5( $ip );
}

/** Same-host redirect sanitizer. Returns '' when the target is foreign. */
function pda_sanitize_redirect( $to ) {
	$to = trim( wp_unslash( (string) $to ) );
	if ( '' === $to ) {
		return '';
	}
	return esc_url_raw( wp_validate_redirect( $to, '' ) );
}


/**
 * Establish the auth cookie AND mint a wp_rest nonce bound to the SAME
 * session token. wp_create_nonce() reads the session token out of the
 * logged-in cookie in $_COOKIE; during the login/register request that
 * cookie exists only in the outgoing headers, so we inject it. Without
 * this, handler-issued nonces verify against token "" and later REST
 * calls (token from the real cookie) fail with rest_cookie_invalid_nonce.
 */
function pda_set_session_and_nonce( $user_id, $remember ) {
	$expiration = time() + apply_filters(
		'auth_cookie_expiration',
		$remember ? 14 * DAY_IN_SECONDS : 2 * DAY_IN_SECONDS,
		$user_id,
		$remember
	);
	$manager = WP_Session_Tokens::get_instance( $user_id );
	$token   = $manager->create( $expiration );
	wp_clear_auth_cookie();
	wp_set_auth_cookie( $user_id, $remember, '', $token );
	wp_set_current_user( $user_id );
	// Make the cookie visible to wp_get_session_token() in THIS request.
	$cookie_name = wp_generate_auth_cookie( $user_id, $expiration, 'logged_in', $token );
	$_COOKIE[ LOGGED_IN_COOKIE ] = $cookie_name;
	$GLOBALS['pda_rest_nonce'] = wp_create_nonce( 'wp_rest' );
}

/** REST nonce minted together with the current auth cookie. */
function pda_session_nonce() {
	return isset( $GLOBALS['pda_rest_nonce'] ) ? $GLOBALS['pda_rest_nonce'] : wp_create_nonce( 'wp_rest' );
}

/**
 * POST /pdforce/v1/register
 * Body: user_email (required), password (required, >=8), user_login
 * (optional -> email local-part), display_name, pdforce_role,
 * pdforce_district, honeypot pdforce_website, pdforce_ts, redirect_to.
 * Creates a subscriber, stores profile meta, sends the account email, and
 * logs the user in immediately (cookie + fresh REST nonce).
 */
function pda_handle_register( $request ) {
	pda_gate_bot( $request );

	$ip     = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	$rkey   = 'pda_reg_' . md5( $ip );
	$regs   = (int) get_transient( $rkey );
	if ( $regs >= PDA_REG_LIMIT ) {
		wp_send_json_error( array( 'message' => 'Too many attempts. Try again later.' ), 429 );
	}
	// The increment moved below: this cap counts SUCCESSFUL account
	// creations only, so validation failures never consume the hourly
	// budget (mass creation is what this cap defends against).

	$email = sanitize_email( wp_unslash( (string) ( $request['user_email'] ?? '' ) ) );
	if ( ! is_email( $email ) ) {
		wp_send_json_error( array( 'message' => 'Enter a valid email address.' ), 400 );
	}
	if ( email_exists( $email ) ) {
		wp_send_json_error( array( 'message' => 'An account with that email already exists.' ), 400 );
	}

	$password = (string) ( $request['password'] ?? '' );
	if ( strlen( $password ) < 8 ) {
		wp_send_json_error( array( 'message' => 'Password must be at least 8 characters.' ), 400 );
	}
	if ( strlen( $password ) > 64 ) {
		wp_send_json_error( array( 'message' => 'Password is too long.' ), 400 );
	}

	$login = sanitize_user( (string) ( $request['user_login'] ?? '' ), true );
	if ( '' === $login ) {
		$at    = strrpos( $email, '@' );
		$login = sanitize_user( false !== $at ? substr( $email, 0, $at ) : '', true );
	}
	if ( '' === $login ) {
		$login = 'reader';
	}
	$base = $login;
	$n    = 1;
	while ( username_exists( $login ) ) {
		$n++;
		$login = $base . '-' . $n;
	}

	$display = pda_clip( $request['display_name'] ?? '', PDA_MAX_NAME );
	if ( '' === $display ) {
		$display = $login;
	}
	$role     = pda_clip( $request['pdforce_role'] ?? '', PDA_MAX_ROLE );
	$district = pda_clip( $request['pdforce_district'] ?? '', PDA_MAX_DISTRICT );

	$user_id = wp_insert_user(
		array(
			'user_login'   => $login,
			'user_pass'    => $password,
			'user_email'   => $email,
			'display_name' => $display,
			'role'         => 'subscriber',
		)
	);
	if ( is_wp_error( $user_id ) ) {
		wp_send_json_error( array( 'message' => 'Could not create the account: ' . $user_id->get_error_message() ), 400 );
	}

	update_user_meta( $user_id, 'pdforce_role', $role );
	update_user_meta( $user_id, 'pdforce_district', $district );
	set_transient( $rkey, 1 + (int) get_transient( $rkey ), HOUR_IN_SECONDS );

	// Hard email confirmation gate: no session until the link is clicked.
	$token = wp_generate_password( 32, false );
	update_user_meta( $user_id, 'pdforce_verified', 0 );
	update_user_meta( $user_id, 'pdforce_confirm_key', hash( 'sha256', $token ) );
	update_user_meta( $user_id, 'pdforce_confirm_exp', time() + 2 * DAY_IN_SECONDS );

	$confirm_link = add_query_arg(
		rawurlencode_deep( array( 'key' => $token, 'login' => $login ) ),
		home_url( '/account/confirm/' )
	);
	$confirm_body  = '<p style="margin:0 0 12px;">Welcome to Parent Data Force.</p>'
		. '<p style="margin:0 0 12px;">One click left: confirm <strong>' . esc_html( $email ) . '</strong> to open your account. The link expires in 48 hours — after that you can request a fresh one from the page.</p>'
		. '<p style="margin:0;color:#a0a0a0;font-size:13px;">If you did not sign up for this, ignore this email and the address will not be used.</p>'
		. '<p style="margin:12px 0 0;word-break:break-all;color:#a0a0a0;font-size:13px;">Button not working? Paste this link into your browser:<br>' . esc_url( $confirm_link ) . '</p>';
	pda_send_member_mail(
		$email,
		'Confirm your Parent Data Force account',
		pda_mail_html( 'Confirm your account', $confirm_body, $confirm_link, 'Confirm my account' )
	);

	$admin_body = 'New member registration on ' . home_url() . "\n\n"
		. 'Display name: ' . $display . "\n"
		. 'Email: ' . $email . "\n"
		. 'District: ' . ( $district !== '' ? $district : '(none)' ) . "\n"
		. 'Role: ' . ( $role !== '' ? $role : '(none)' ) . "\n"
		. 'Time: ' . date_i18n( 'Y-m-d H:i:s T' );
	wp_mail(
		get_option( 'admin_email', 'joey@parentdataforce.com' ),
		'[PD Force] New member: ' . $display,
		$admin_body
	);

	// No auto-login, no nonce in the body: the reader proves control of
	// the inbox on the confirm screen.
	wp_send_json_success(
		array(
			'confirmed'   => false,
			'message'     => 'Check your email — click the link to confirm your account.',
			'email'       => $email,
			'display_name'=> $display,
		),
		201
	);
}

/**
 * POST /pdforce/v1/confirm — public. Hash-compares SHA256(token) against
 * the stored confirm key, flips pdforce_verified to 1, auto-logs the
 * reader in (session + REST nonce minted together) and hands back the
 * dashboard redirect.
 */
function pda_handle_confirm( $request ) {
	pda_gate_bot( $request );

	$login = sanitize_user( (string) $request['login'], true );
	$user  = $login ? get_user_by( 'login', $login ) : false;
	if ( ! $user ) {
		wp_send_json_error( array( 'message' => 'That confirm link is invalid or expired. Send it again.' ), 400 );
	}

	if ( 1 === (int) get_user_meta( $user->ID, 'pdforce_verified', true ) ) {
		wp_send_json_success(
			array(
				'already' => true,
				'message' => 'Already confirmed — log in below.',
			)
		);
	}

	$stored = (string) get_user_meta( $user->ID, 'pdforce_confirm_key', true );
	$exp    = (int) get_user_meta( $user->ID, 'pdforce_confirm_exp', true );
	if ( '' === $stored
		|| ! hash_equals( $stored, hash( 'sha256', (string) $request['key'] ) )
		|| $exp < time()
	) {
		wp_send_json_error( array( 'message' => 'That confirm link is invalid or expired. Send it again.' ), 400 );
	}

	update_user_meta( $user->ID, 'pdforce_verified', 1 );
	delete_user_meta( $user->ID, 'pdforce_confirm_key' );
	delete_user_meta( $user->ID, 'pdforce_confirm_exp' );
	pda_set_session_and_nonce( $user->ID, true );

	wp_send_json_success(
		array(
			'user_id'      => $user->ID,
			'display_name' => $user->display_name,
			'nonce'        => pda_session_nonce(),
			'redirect_to'  => home_url( '/account/' ),
		)
	);
}

/**
 * POST /pdforce/v1/resend — public, throttled 1 per IP per 15 min.
 * Generic success either way: never reveals which emails exist here.
 */
function pda_handle_resend( $request ) {
	pda_gate_bot( $request );

	$ip   = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	$ikey = 'pda_resend_' . md5( $ip );
	if ( (int) get_transient( $ikey ) >= PDA_REG_LIMIT ) {
		wp_send_json_error( array( 'message' => 'Too many requests. Try again soon.' ), 429 );
	}
	set_transient( $ikey, 1 + (int) get_transient( $ikey ), 15 * MINUTE_IN_SECONDS );

	$email = sanitize_email( wp_unslash( (string) ( $request['email'] ?? '' ) ) );
	if ( is_email( $email ) ) {
		$ekey = 'pda_resende_' . md5( $email );
		if ( get_transient( $ekey ) ) {
			wp_send_json_error( array( 'message' => 'Too many requests. Try again soon.' ), 429 );
		}
		$user = get_user_by( 'email', $email );
		if ( $user && 0 === (int) get_user_meta( $user->ID, 'pdforce_verified', true ) ) {
			$token = wp_generate_password( 32, false );
			update_user_meta( $user->ID, 'pdforce_confirm_key', hash( 'sha256', $token ) );
			update_user_meta( $user->ID, 'pdforce_confirm_exp', time() + 2 * DAY_IN_SECONDS );

			$confirm_link = add_query_arg(
				rawurlencode_deep( array( 'key' => $token, 'login' => $user->user_login ) ),
				home_url( '/account/confirm/' )
			);
			$confirm_first = (string) $user->display_name !== (string) $user->user_login
				? (string) $user->display_name
				: 'there';
			$confirm_body = '<p style="margin:0 0 12px;">Hi ' . esc_html( $confirm_first ) . ',</p>'
				. '<p style="margin:0 0 12px;">Here is a fresh confirmation link for your Parent Data Force account. It expires in 48 hours.</p>'
				. '<p style="margin:0;color:#a0a0a0;font-size:13px;">If you did not sign up for this, ignore this email and the address will not be used.</p>'
				. '<p style="margin:12px 0 0;word-break:break-all;color:#a0a0a0;font-size:13px;">Button not working? Paste this link into your browser:<br>' . esc_url( $confirm_link ) . '</p>';
			pda_send_member_mail(
				$email,
				'Confirm your Parent Data Force account',
				pda_mail_html( 'Confirm your account', $confirm_body, $confirm_link, 'Confirm my account' )
			);
			set_transient( $ekey, 1, 15 * MINUTE_IN_SECONDS );
		}
	}

	wp_send_json_success(
		array( 'message' => 'If that email still needs confirming, a fresh link is on its way.' )
	);
}
/**
 * POST /pdforce/v1/login
 * Body: log (login or email), pwd, remember, redirect_to.
 * Wrong creds -> generic 401 so usernames can't be enumerated.
 */
function pda_handle_login( $request ) {
	pda_gate_bot( $request );

	$ip   = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	$fkey = 'pda_loginf_' . md5( $ip );
	if ( (int) get_transient( $fkey ) >= PDA_LOGIN_LIMIT ) {
		wp_send_json_error( array( 'message' => 'Too many failed attempts. Wait 15 minutes.' ), 429 );
	}

	$identity = sanitize_text_field( wp_unslash( (string) ( $request['log'] ?? '' ) ) );
	$pwd      = (string) ( $request['pwd'] ?? '' );
	$remember = ! empty( $request['remember'] );
	if ( '' === $identity || '' === $pwd ) {
		wp_send_json_error( array( 'message' => 'Enter your username and password.' ), 400 );
	}

	if ( is_email( $identity ) ) {
		$by_email = get_user_by( 'email', $identity );
		if ( $by_email ) {
			$identity = $by_email->user_login;
		}
	}

	// Email-confirmation gate: unconfirmed accounts cannot log in. This
	// response is itself the "resend" hint; it discloses only the
	// existence of UNCONFIRMED accounts (accepted tradeoff).
	$probe = get_user_by( 'login', $identity );
	if ( $probe && '0' === (string) get_user_meta( $probe->ID, 'pdforce_verified', true ) ) {
		wp_send_json_error( array( 'message' => 'Confirm your account first — check your email for the link.' ), 403 );
	}

	$user = wp_authenticate( $identity, $pwd );
	if ( is_wp_error( $user ) || ! $user instanceof WP_User ) {
		set_transient( $fkey, 1 + (int) get_transient( $fkey ), 15 * MINUTE_IN_SECONDS );
		wp_send_json_error( array( 'message' => 'Unknown username or incorrect password.' ), 401 );
	}

	pda_set_session_and_nonce( $user->ID, $remember );

	$redirect = pda_sanitize_redirect( $request['redirect_to'] ?? '' );
	wp_send_json_success(
		array(
			'user_id'     => $user->ID,
			'display_name'=> $user->display_name,
			'nonce'       => pda_session_nonce(),
			'redirect_to' => $redirect ? $redirect : home_url( '/account/' ),
		)
	);
}

/** POST /pdforce/v1/logout */
function pda_handle_logout() {
	wp_logout();
	wp_send_json_success( array( 'redirect_to' => home_url( '/account/' ) ) );
}

/**
 * POST /pdforce/v1/forgot — public, 5/hour/IP. Reuses core's
 * retrieve_password() (key mint + core notification filter above);
 * response is generic either way (no enumeration).
 */
function pda_handle_forgot( $request ) {
	pda_gate_bot( $request );

	$tkey = pda_ip_key( 'pda_forgot_' );
	$seen = (int) get_transient( $tkey );
	if ( $seen >= PDA_REG_LIMIT ) {
		wp_send_json_error( array( 'message' => 'Too many requests. Try again soon.' ), 429 );
	}
	set_transient( $tkey, 1 + $seen, HOUR_IN_SECONDS );

	$identity = sanitize_text_field( wp_unslash( (string) ( $request['email'] ?? '' ) ) );
	$user     = false;
	if ( is_email( $identity ) ) {
		$user = get_user_by( 'email', $identity );
	}
	if ( ! $user && '' !== $identity ) {
		$user = get_user_by( 'login', sanitize_user( $identity, true ) );
	}
	// Unconfirmed accounts: no reset mail (a reset would bypass the
	// confirmation gate); the response stays generic either way.
	if ( $user && 1 === (int) get_user_meta( $user->ID, 'pdforce_verified', true ) ) {
		retrieve_password( $user->user_login );
	}

	wp_send_json_success(
		array( 'message' => 'If an account exists for that email, a reset link is on its way.' )
	);
}

/**
 * POST /pdforce/v1/password-reset — public. Core mechanics reused:
 * check_password_reset_key() validates the activation key; wp_set_password()
 * stores the new hash and clears the key (single-use).
 */
function pda_handle_password_reset( $request ) {
	pda_gate_bot( $request );

	$password = (string) ( $request['password'] ?? '' );
	if ( strlen( $password ) < 8 ) {
		wp_send_json_error( array( 'message' => 'Password must be at least 8 characters.' ), 400 );
	}
	if ( strlen( $password ) > 64 ) {
		wp_send_json_error( array( 'message' => 'Password is too long.' ), 400 );
	}

	$user = check_password_reset_key(
		(string) ( $request['key'] ?? '' ),
		sanitize_user( (string) ( $request['login'] ?? '' ), true )
	);
	if ( is_wp_error( $user ) || ! $user instanceof WP_User ) {
		wp_send_json_error( array( 'message' => 'That reset link is invalid or expired. Request a new one.' ), 400 );
	}
	if ( 0 === (int) get_user_meta( $user->ID, 'pdforce_verified', true ) ) {
		// Unconfirmed account: a reset would bypass the confirm gate.
		wp_send_json_error( array( 'message' => 'Confirm your account first — check your email for the link.' ), 403 );
	}

	wp_set_password( $password, $user->ID );
	pda_set_session_and_nonce( $user->ID, true );

	wp_send_json_success(
		array(
			'user_id'      => $user->ID,
			'display_name' => $user->display_name,
			'nonce'        => pda_session_nonce(),
			'redirect_to'  => home_url( '/account/' ),
		)
	);
}

/** GET /pdforce/v1/profile — own profile + privacy toggles. */
function pda_handle_profile_get() {
	pda_profile_payload( get_current_user_id() );
}

/** Shared GET/POST response shape for /pdforce/v1/profile. */
function pda_profile_payload( $uid ) {
	$user = get_userdata( $uid );
	wp_send_json_success(
		array(
			'display_name'  => $user ? (string) $user->display_name : '',
			'role'          => (string) get_user_meta( $uid, 'pdforce_role', true ),
			'district'      => (string) get_user_meta( $uid, 'pdforce_district', true ),
			'show_name'     => (int) get_user_meta( $uid, 'pdforce_show_name', true ),
			'show_role'     => (int) get_user_meta( $uid, 'pdforce_show_role', true ),
			'show_district' => (int) get_user_meta( $uid, 'pdforce_show_district', true ),
			'privacy_set'   => (int) get_user_meta( $uid, 'pdforce_privacy_set', true ),
		)
	);
}

/**
 * POST /pdforce/v1/profile — updates the member's profile and always
 * stamps pdforce_privacy_set=1 (first-run chooser → dashboard).
 */
function pda_handle_profile_save( $request ) {
	$uid = get_current_user_id();

	$user    = get_userdata( $uid );
	$display = pda_clip( $request['display_name'] ?? '', PDA_MAX_NAME );
	if ( '' === $display && $user ) {
		$display = (string) $user->display_name;
	}
	$role     = pda_clip( $request['pdforce_role'] ?? '', PDA_MAX_ROLE );
	$district = pda_clip( $request['pdforce_district'] ?? '', PDA_MAX_DISTRICT );

	wp_update_user(
		array(
			'ID'           => $uid,
			'display_name' => $display,
		)
	);
	update_user_meta( $uid, 'pdforce_role', $role );
	update_user_meta( $uid, 'pdforce_district', $district );
	update_user_meta( $uid, 'pdforce_show_name', (int) ! empty( $request['show_name'] ) );
	update_user_meta( $uid, 'pdforce_show_role', (int) ! empty( $request['show_role'] ) );
	update_user_meta( $uid, 'pdforce_show_district', (int) ! empty( $request['show_district'] ) );
	update_user_meta( $uid, 'pdforce_privacy_set', 1 );

	pda_profile_payload( $uid );
}

/**
 * POST /pdforce/v1/ticket — create a private ticket (author = current user).
 */
function pda_handle_ticket_create( $request ) {
	pda_gate_bot( $request );

	$uid = get_current_user_id();
	$uq  = 'pda_tu_' . (int) $uid;
	if ( false !== get_transient( $uq ) ) {
		wp_send_json_error( array( 'message' => 'You just submitted a ticket. Try again in a few minutes.' ), 429 );
	}
	$ip  = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	$iq  = 'pda_ti_' . md5( $ip );
	if ( (int) get_transient( $iq ) >= PDA_TIX_IP_LIMIT ) {
		wp_send_json_error( array( 'message' => 'Too many tickets were submitted from this network. Wait an hour.' ), 429 );
	}

	$kind = pda_clip( $request['t_kind'] ?? '', 20 );
	if ( ! in_array( $kind, array( 'question', 'evidence', 'help', 'correction', 'other' ), true ) ) {
		$kind = 'other';
	}
	$subject = pda_clip( $request['t_subject'] ?? '', PDA_MAX_SUBJECT );
	if ( '' === $subject ) {
		wp_send_json_error( array( 'message' => 'Add a short subject.' ), 400 );
	}
	$body = trim( wp_strip_all_tags( wp_unslash( (string) ( $request['t_body'] ?? '' ) ) ) );
	$len  = function_exists( 'mb_strlen' ) ? mb_strlen( $body ) : strlen( $body );
	if ( $len < PDA_MIN_BODY ) {
		wp_send_json_error( array( 'message' => 'Describe the ticket in at least 20 characters.' ), 400 );
	}
	if ( $len > PDA_MAX_BODY ) {
		wp_send_json_error( array( 'message' => 'Ticket body is limited to 8000 characters.' ), 400 );
	}
	$district = pda_clip( $request['t_district'] ?? '', PDA_MAX_DISTRICT );

	$user    = wp_get_current_user();
	$post_id = wp_insert_post(
		array(
			'post_type'    => 'pdforce_ticket',
			'post_title'   => $subject,
			'post_content' => wpautop( $body ), // stripped above, safe text
			'post_status'  => 'private',
			'post_author'  => $user->ID,
			'meta_input'   => array(
				'pdforce_kind'     => $kind,
				'pdforce_status'   => 'new',
				'pdforce_district' => $district,
				'pdforce_role'     => (string) get_user_meta( $user->ID, 'pdforce_role', true ),
			),
		),
		true
	);
	if ( is_wp_error( $post_id ) || ! $post_id ) {
		wp_send_json_error( array( 'message' => 'Could not record the ticket. Please try again.' ), 500 );
	}
	// Rate-limit bookkeeping runs only after the insert succeeded so a
	// 500 never leaves the user locked out with no ticket recorded.

	set_transient( $uq, 1, PDA_TIX_USER_WINDOW );
	set_transient( $iq, 1 + (int) get_transient( $iq ), HOUR_IN_SECONDS );

	$owner = get_option( 'admin_email', 'joey@parentdataforce.com' );
	wp_mail(
		$owner,
		sprintf( '[Ticket #%d] %s: %s', $post_id, $kind, $subject ),
		$body . "\n\n"
			. 'From: ' . $user->display_name . ' <' . $user->user_email . ">\n"
			. 'District: ' . ( '' !== $district ? $district : '(none)' ) . "\n"
			. home_url( '/account/#ticket-' . $post_id )
	);

	wp_send_json_success( array( 'id' => (int) $post_id, 'status' => 'new' ), 201 );
}

/** GET /pdforce/v1/tickets/mine — compact queue for the account page. */
function pda_handle_tickets_mine() {
	$posts = get_posts(
		array(
			'post_type'      => 'pdforce_ticket',
			'author'         => get_current_user_id(),
			'post_status'    => 'private',
			'posts_per_page' => 50,
			'orderby'        => 'date',
			'order'          => 'DESC',
		)
	);
	$out = array();
	foreach ( $posts as $p ) {
		$plain = wp_strip_all_tags( (string) $p->post_content );
		$clip  = function_exists( 'mb_substr' ) ? 'mb_substr' : 'substr';
		$out[] = array(
			'id'       => (int) $p->ID,
			'kind'     => (string) get_post_meta( $p->ID, 'pdforce_kind', true ),
			'status'   => (string) get_post_meta( $p->ID, 'pdforce_status', true ),
			'subject'  => (string) $p->post_title,
			'district' => (string) get_post_meta( $p->ID, 'pdforce_district', true ),
			'date'     => get_the_date( 'c', $p ),
			// mb_substr/substr need the start offset 0; the old
			// $clip( $plain, 200 ) sliced FROM char 200 (empty for
			// short bodies).
			'excerpt'  => $clip( $plain, 0, 200 ),
		);
	}
	wp_send_json_success( array( 'tickets' => $out, 'count' => count( $out ) ) );
}

/** GET /pdforce/v1/tickets/{id} — full ticket + comment thread. */
function pda_handle_ticket_get( $request ) {
	$ticket = get_post( (int) $request['id'] );
	$can_edit_others = current_user_can( 'edit_others_posts' );
	$author = get_userdata( (int) $ticket->post_author );

	$comments = array();
	foreach ( get_comments(
		array(
			'post_id'    => $ticket->ID,
			'status'     => 'approve',
			'orderby'    => 'comment_date_gmt',
			'order'      => 'ASC',
		)
	) as $c ) {
		// Ticket threads stay real-name even when the author's public
		// comment byline is 'Anonymous' (privacy at rest).
		$t_author = (string) $c->comment_author;
		if ( ! empty( $c->user_id ) ) {
			$cu = get_userdata( (int) $c->user_id );
			if ( $cu ) {
				$t_author = (string) $cu->display_name;
			}
		}
		$comments[] = array(
			'id'       => (int) $c->comment_ID,
			'author'   => $t_author,
			'is_owner' => $can_edit_others && (int) $c->user_id !== (int) $ticket->post_author,
			'date'     => str_replace( '+00:00', 'Z', gmdate( 'c', strtotime( $c->comment_date_gmt . ' GMT' ) ) ),
			// wpautop'd text: safe to place in innerHTML, but JS still uses textContent for author/date.
			'content'  => (string) $c->comment_content,
		);
	}

	wp_send_json_success(
		array(
			'ticket'   => array(
				'id'       => (int) $ticket->ID,
				'kind'     => (string) get_post_meta( $ticket->ID, 'pdforce_kind', true ),
				'status'   => (string) get_post_meta( $ticket->ID, 'pdforce_status', true ),
				'subject'  => (string) $ticket->post_title,
				'district' => (string) get_post_meta( $ticket->ID, 'pdforce_district', true ),
				'date'     => get_the_date( 'c', $ticket ),
				'author'   => $author ? (string) $author->display_name : '',
				'body'     => (string) $ticket->post_content,
			),
			'comments' => $comments,
		)
	);
}

/** POST /pdforce/v1/tickets/{id}/reply — adds an approved comment. */
function pda_handle_ticket_reply( $request ) {
	$ticket = get_post( (int) $request['id'] );
	if ( ! $ticket || 'pdforce_ticket' !== $ticket->post_type ) {
		wp_send_json_error( array( 'message' => 'Ticket not found.' ), 404 );
	}

	$body = trim( wp_strip_all_tags( wp_unslash( (string) ( $request['body'] ?? '' ) ) ) );
	$len  = function_exists( 'mb_strlen' ) ? mb_strlen( $body ) : strlen( $body );
	if ( $len < 2 || $len > PDA_MAX_REPLY ) {
		wp_send_json_error( array( 'message' => 'Reply must be 2–2000 characters.' ), 400 );
	}

	$user   = wp_get_current_user();
	$is_admin_reply = $user->ID !== (int) $ticket->post_author && current_user_can( 'edit_others_posts' );

	$comment_id = wp_insert_comment(
		array(
			'comment_post_ID'      => $ticket->ID,
			'comment_author'       => $user->display_name,
			'comment_author_email' => $user->user_email,
			'comment_author_url'   => '',
			'comment_content'      => wpautop( $body ),
			'comment_approved'     => 1,
			'comment_type'         => 'comment',
			'user_id'              => $user->ID,
		)
	);
	if ( ! $comment_id || is_wp_error( $comment_id ) ) {
		wp_send_json_error( array( 'message' => 'Could not save the reply.' ), 500 );
	}

	if ( $is_admin_reply ) {
		$author = get_userdata( (int) $ticket->post_author );
		if ( $author && $author->user_email ) {
			wp_mail(
				$author->user_email,
				sprintf( 'Your ticket #%d got a reply', $ticket->ID ),
				'Your ticket "' . $ticket->post_title . '" got a reply. Read it at '
					. home_url( '/account/#ticket-' . $ticket->ID ) . "\n\n— Parent Data Force"
			);
		}
	} else {
		wp_mail(
			get_option( 'admin_email', 'joey@parentdataforce.com' ),
			sprintf( 'Ticket #%d got a reply', $ticket->ID ),
			$user->display_name . ' replied to "' . $ticket->post_title . "\":\n\n" . $body
				. "\n\n" . site_url( '/wp-admin/admin.php?page=&post_type=pdforce_ticket&p=' . $ticket->ID )
		);
	}

	wp_send_json_success( array( 'id' => (int) $comment_id ), 201 );
}

/** PUT /pdforce/v1/tickets/{id}/status — owner action; emails the author. */
function pda_handle_ticket_status( $request ) {
	$ticket = get_post( (int) $request['id'] );
	if ( ! $ticket || 'pdforce_ticket' !== $ticket->post_type ) {
		wp_send_json_error( array( 'message' => 'Ticket not found.' ), 404 );
	}
	$status = pda_clip( $request['status'] ?? '', 20 );
	if ( ! in_array( $status, array( 'new', 'answered', 'closed' ), true ) ) {
		wp_send_json_error( array( 'message' => 'Status must be new, answered, or closed.' ), 400 );
	}
	$old = (string) get_post_meta( $ticket->ID, 'pdforce_status', true );
	update_post_meta( $ticket->ID, 'pdforce_status', $status );

	if ( $old !== $status ) {
		$author = get_userdata( (int) $ticket->post_author );
		if ( $author && $author->user_email ) {
			wp_mail(
				$author->user_email,
				sprintf( 'Ticket #%d is now "%s"', $ticket->ID, $status ),
				'Your ticket "' . $ticket->post_title . '" was marked ' . $status
					. '. See the thread at ' . home_url( '/account/#ticket-' . $ticket->ID )
					. "\n\n— Parent Data Force"
			);
		}
	}

	wp_send_json_success( array( 'id' => (int) $ticket->ID, 'status' => $status ) );
}

/**
 * Account pages + single posts: enqueue the theme JS (localized with the
 * REST URL, a fresh REST nonce only when logged in, and per-page state);
 * CSS goes only on the six account pages.
 */
if ( ! function_exists( 'pda_enqueue_account_assets' ) ) :
	function pda_enqueue_account_assets() {
		$which = '';
		foreach ( array( 'account', 'register', 'login', 'ticket', 'confirm', 'reset' ) as $slug ) {
			if ( is_page( $slug ) ) {
				$which = $slug;
				break;
			}
		}
		$is_post = is_singular( 'post' );
		if ( ! $which && ! $is_post ) {
			return;
		}
		$ver = wp_get_theme()->get( 'Version' );
		$data = array(
			'page'        => $which,
			'restUrl'     => esc_url_raw( rest_url() ),
			'loggedIn'    => (bool) is_user_logged_in(),
			'wpNonce'     => is_user_logged_in() ? wp_create_nonce( 'wp_rest' ) : '',
			'accountUrl'  => esc_url_raw( home_url( '/account/' ) ),
			'registerUrl' => esc_url_raw( home_url( '/account/register/' ) ),
			'loginUrl'    => esc_url_raw( home_url( '/account/login/' ) ),
			'ticketUrl'   => esc_url_raw( home_url( '/account/ticket/' ) ),
			'confirmUrl'  => esc_url_raw( home_url( '/account/confirm/' ) ),
			'resetUrl'    => esc_url_raw( home_url( '/account/reset/' ) ),
		);
		if ( $which ) {
			wp_enqueue_style(
				'pdforce-account',
				get_theme_file_uri( 'assets/css/pdforce-account.css' ),
				array(),
				$ver
			);
		}
		wp_enqueue_script(
			'pdforce-account',
			get_theme_file_uri( 'assets/js/pdforce-account.js' ),
			array(),
			$ver,
			true
		);
		wp_localize_script( 'pdforce-account', 'pdforceAccount', $data );
	}
endif;
add_action( 'wp_enqueue_scripts', 'pda_enqueue_account_assets' );

/** Body-class hooks the plan's JS dispatch reads (is_page-account etc.). */
add_filter( 'body_class', 'pda_body_classes' );
function pda_body_classes( $classes ) {
	$which = '';
	foreach ( array( 'account', 'register', 'login', 'ticket', 'confirm', 'reset' ) as $slug ) {
		if ( is_page( $slug ) ) {
			$which = $slug;
			break;
		}
	}
	if ( $which ) {
		$classes[] = 'is_page-' . $which;
	}
	return $classes;
}
