<?php
/**
 * Plugin Name: PDF — Settlement Request Queue Intake
 * Description: Private pdforce_queue_note post type plus a public REST intake
 *              route (POST /pdforce/v1/queue) for the MA Student Settlement
 *              Records district queue. Deployed as mu-plugin:
 *              /public_html/news/wp-content/mu-plugins/pdforce-queue.php
 * Version:     1.1.0
 *
 * Intake shape (application/x-www-form-urlencoded):
 *   POST /pdforce/v1/queue      — district submission (below)
 *   POST /pdforce/v1/queue/vote — interest vote on a queued district
 *   pdq_district  required, <= 120 chars
 *   pdq_town      optional, <= 120 chars (submission only)
 *   pdq_note      optional, <= 400 chars (submission only)
 *   pdq_ts        required, epoch seconds stamped by the form at submit time
 *   pdq_website   honeypot — must stay empty
 *
 * Stored as private pdforce_queue_note posts:
 *   title   = district
 *   content = "district|town|note" for submissions, "vote|district" for votes
 *             (pipe-delimited, parsed by `settlements_db.py queue-ingest`,
 *             which then marks pdforce_ingested = 1 via REST meta)
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const PDQ_MAX_TEXT    = 120;
const PDQ_MAX_NOTE    = 400;
const PDQ_TIME_FLOOR  = 3;   // seconds of past clock drift tolerated
const PDQ_TIME_CEIL   = 60;  // seconds of future clock skew tolerated
const PDQ_RATE_WINDOW = 60;  // seconds between submissions per IP

/**
 * Private, REST-visible custom post type for queue intake.
 */
add_action( 'init', 'pdq_register_queue_post_type' );
function pdq_register_queue_post_type() {
	register_post_type(
		'pdforce_queue_note',
		array(
			'labels'          => array(
				'name'          => 'Queue notes',
				'singular_name' => 'Queue note',
			),
			'public'          => false,
			'show_in_rest'    => true,
			'rest_base'       => 'queue-notes',
			'supports'        => array( 'title', 'editor', 'custom-fields' ),
			'capability_type' => 'post',
			'map_meta_cap'    => true,
		)
	);

	register_post_meta(
		'pdforce_queue_note',
		'pdforce_ingested',
		array(
			'show_in_rest' => true,
			'single'       => true,
			'type'         => 'integer',
			'default'      => 0,
		)
	);
}

/**
 * Public intake route. No authentication: visitors may queue a district.
 */
add_action( 'rest_api_init', 'pdq_register_queue_route' );
function pdq_register_queue_route() {
	register_rest_route(
		'pdforce/v1',
		'/queue',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pdq_handle_queue_submission',
		)
	);

	register_rest_route(
		'pdforce/v1',
		'/queue/vote',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'pdq_handle_queue_vote',
		)
	);
}

/**
 * Sanitize and clip a text parameter to a hard length cap.
 */
function pdq_clip( $value, $max ) {
	$value = sanitize_text_field( wp_unslash( (string) $value ) );
	$clip  = function_exists( 'mb_substr' ) ? 'mb_substr' : 'substr';
	return $clip( $value, 0, $max );
}

/**
 * Intake callback: gate -> sanitize -> store as private post.
 */
function pdq_handle_queue_submission( $request ) {
	// Honeypot: real users never see this field; bots that fill it are
	// silently dropped without revealing why.
	if ( ! empty( $request['pdq_website'] ) ) {
		wp_send_json_error( null, 400 );
	}

	// Time floor: the form stamps pdq_ts at submit time; a bot replaying a
	// captured request (or skipping JS) has no fresh stamp.
	$ts  = (int) ( $request['pdq_ts'] ?? 0 );
	$now = time();
	if ( $ts < $now - PDQ_TIME_FLOOR || $ts > $now + PDQ_TIME_CEIL ) {
		wp_send_json_error( null, 400 );
	}

	// Rate limit: one submission per IP per window.
	$ip       = isset( $_SERVER['REMOTE_ADDR'] ) ? md5( (string) $_SERVER['REMOTE_ADDR'] ) : '';
	$rate_key = 'pdq_rate_' . $ip;
	if ( false !== get_transient( $rate_key ) ) {
		wp_send_json_error( array( 'message' => 'Slow down.' ), 429 );
	}

	$district = pdq_clip( $request['pdq_district'] ?? '', PDQ_MAX_TEXT );
	$town     = pdq_clip( $request['pdq_town'] ?? '', PDQ_MAX_TEXT );
	$note     = pdq_clip( $request['pdq_note'] ?? '', PDQ_MAX_NOTE );

	if ( '' === $district ) {
		wp_send_json_error( array( 'message' => 'District name is required.' ), 400 );
	}

	set_transient( $rate_key, 1, PDQ_RATE_WINDOW );

	$post_id = wp_insert_post(
		array(
			'post_type'    => 'pdforce_queue_note',
			'post_title'   => $district,
			'post_content' => $district . '|' . $town . '|' . $note,
			'post_status'  => 'private',
		),
		true
	);

	if ( is_wp_error( $post_id ) || ! $post_id ) {
		wp_send_json_error(
			array( 'message' => 'Could not record the submission. Please try again.' ),
			500
		);
	}

	wp_send_json_success(
		array( 'message' => 'Queued. It will appear here at the next refresh.' ),
		200
	);
}

/**
 * Vote handler: same gates as intake, but rate-limited per district per IP
 * (one vote per district per hour per IP) so a reader can vote for several
 * districts in a row without hitting the intake window.
 */
function pdq_handle_queue_vote( $request ) {
	// Honeypot: same trap as intake.
	if ( ! empty( $request['pdq_website'] ) ) {
		wp_send_json_error( null, 400 );
	}

	// Time floor: vote buttons stamp pdq_ts at click time.
	$ts  = (int) ( $request['pdq_ts'] ?? 0 );
	$now = time();
	if ( $ts < $now - PDQ_TIME_FLOOR || $ts > $now + PDQ_TIME_CEIL ) {
		wp_send_json_error( null, 400 );
	}

	$district = pdq_clip( $request['pdq_district'] ?? '', PDQ_MAX_TEXT );
	if ( '' === $district ) {
		wp_send_json_error( array( 'message' => 'District name is required.' ), 400 );
	}

	// Rate limit: one vote per district per hour per IP.
	$ip       = isset( $_SERVER['REMOTE_ADDR'] ) ? md5( (string) $_SERVER['REMOTE_ADDR'] ) : '';
	$vote_key = 'pdq_vrate_' . md5( $ip . '|' . strtolower( $district ) );
	if ( false !== get_transient( $vote_key ) ) {
		wp_send_json_error(
			array( 'message' => 'Already voted for this district recently.' ),
			429
		);
	}

	set_transient( $vote_key, 1, HOUR_IN_SECONDS );

	$post_id = wp_insert_post(
		array(
			'post_type'    => 'pdforce_queue_note',
			'post_title'   => $district,
			'post_content' => 'vote|' . $district,
			'post_status'  => 'private',
		),
		true
	);

	if ( is_wp_error( $post_id ) || ! $post_id ) {
		wp_send_json_error(
			array( 'message' => 'Could not record the vote. Please try again.' ),
			500
		);
	}

	wp_send_json_success( array( 'message' => 'Vote counted.' ), 200 );
}
