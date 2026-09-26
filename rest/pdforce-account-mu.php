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
 * Version:     1.0.0
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
	set_transient( $rkey, $regs + 1, HOUR_IN_SECONDS );

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
	// Account email (welcome/no password reset forced): same wp_mail path
	// as ticket pings; deliverability checked honestly at deploy time.
	wp_new_user_notification( $user_id, null, 'user' );

	wp_set_current_user( $user_id );
	pda_set_session_and_nonce( $user_id, true );

	$redirect = pda_sanitize_redirect( $request['redirect_to'] ?? '' );
	wp_send_json_success(
		array(
			'user_id'     => $user_id,
			'display_name'=> $display,
			'nonce'       => pda_session_nonce(),
			'redirect_to' => $redirect ? $redirect : home_url( '/account/' ),
		),
		201
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

	$user = wp_signon(
		array(
			'user_login'    => $identity,
			'user_password' => $pwd,
			'remember'      => $remember,
		),
		true
	);
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
	if ( ! in_array( $kind, array( 'data', 'question', 'correction', 'other' ), true ) ) {
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

	set_transient( $uq, 1, PDA_TIX_USER_WINDOW );
	set_transient( $iq, 1 + (int) get_transient( $iq ), HOUR_IN_SECONDS );

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
		$plain     = wp_strip_all_tags( (string) $p->post_content );
		$clip      = function_exists( 'mb_substr' ) ? 'mb_substr' : 'substr';
		$out[] = array(
			'id'       => (int) $p->ID,
			'kind'     => (string) get_post_meta( $p->ID, 'pdforce_kind', true ),
			'status'   => (string) get_post_meta( $p->ID, 'pdforce_status', true ),
			'subject'  => (string) $p->post_title,
			'district' => (string) get_post_meta( $p->ID, 'pdforce_district', true ),
			'date'     => get_the_date( 'c', $p ),
			'excerpt'  => $clip( $plain, 200 ),
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
		$comments[] = array(
			'id'       => (int) $c->comment_ID,
			'author'   => (string) $c->comment_author,
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
 * CSS goes only on the four account pages.
 */
if ( ! function_exists( 'pda_enqueue_account_assets' ) ) :
	function pda_enqueue_account_assets() {
		$which = '';
		foreach ( array( 'account', 'register', 'login', 'ticket' ) as $slug ) {
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
	foreach ( array( 'account', 'register', 'login', 'ticket' ) as $slug ) {
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
