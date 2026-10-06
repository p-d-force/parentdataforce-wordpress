<?php
/**
 * Parent Data Force functions and definitions.
 *
 * @link https://developer.wordpress.org/themes/basics/theme-functions/
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.0
 */

if ( ! function_exists( 'pdforce_post_format_setup' ) ) :
	/**
	 * Adds theme support for post formats.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_post_format_setup() {
		add_theme_support( 'post-formats', array( 'aside', 'audio', 'chat', 'gallery', 'image', 'link', 'quote', 'status', 'video' ) );
	}
endif;
add_action( 'after_setup_theme', 'pdforce_post_format_setup' );

if ( ! function_exists( 'pdforce_editor_style' ) ) :
	/**
	 * Enqueues editor-style.css in the editors.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_editor_style() {
		add_editor_style( 'assets/css/editor-style.css' );
	}
endif;
add_action( 'after_setup_theme', 'pdforce_editor_style' );

if ( ! function_exists( 'pdforce_enqueue_styles' ) ) :
	/**
	 * Enqueues the theme stylesheet on the front.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_enqueue_styles() {
		$suffix = SCRIPT_DEBUG ? '' : '.min';
		$src    = 'style' . $suffix . '.css';

		wp_enqueue_style(
			'pdforce-style',
			get_parent_theme_file_uri( $src ),
			array(),
			wp_get_theme()->get( 'Version' )
		);
		wp_style_add_data(
			'pdforce-style',
			'path',
			get_parent_theme_file_path( $src )
		);
	}
endif;
add_action( 'wp_enqueue_scripts', 'pdforce_enqueue_styles' );

if ( ! function_exists( 'pdforce_enqueue_design_assets' ) ) :
	/**
	 * Enqueues the fault-line design layer (CSS) and the animated ASCII engine
	 * (JS). The engine loads only on views that render a `.pdf-ascii` canvas:
	 * the posts index (home), archives, and the 404 template.
	 *
	 * @since Parent Data Force 1.6
	 *
	 * @return void
	 */
	function pdforce_enqueue_design_assets() {
		$ver = wp_get_theme()->get( 'Version' );

		wp_enqueue_style(
			'pdforce-design',
			get_theme_file_uri( 'assets/css/pdf-design.css' ),
			array( 'pdforce-style' ),
			$ver
		);

		wp_enqueue_script(
			'pdforce-stats-rotate',
			get_theme_file_uri( 'assets/js/pdf-stats-rotate.js' ),
			array(),
			$ver,
			true
		);

		if ( is_home() || is_front_page() || is_archive() || is_404() || is_search() ) {
			// Crack path data must load before the engine consumes it.
			wp_enqueue_script(
				'pdforce-crack-path',
				get_theme_file_uri( 'assets/js/bolt-path.js' ),
				array(),
				$ver,
				true
			);
			wp_enqueue_script(
				'pdforce-ascii',
				get_theme_file_uri( 'assets/js/pdforce-ascii.js' ),
				array( 'pdforce-crack-path' ),
				$ver,
				true
			);
		}
	}
endif;
add_action( 'wp_enqueue_scripts', 'pdforce_enqueue_design_assets' );

if ( ! function_exists( 'pdforce_enqueue_cta_events' ) ) :
	/**
	 * Enqueues the click-event tracking script on every public view. The script
	 * self-scopes to main-content clicks (header/nav/footer excluded) and fires
	 * gtag('event', 'cta_click', ...) against whatever configs the page has.
	 *
	 * @since Parent Data Force 1.9
	 *
	 * @return void
	 */
	function pdforce_enqueue_cta_events() {
		wp_enqueue_script(
			'pdforce-cta-events',
			get_theme_file_uri( 'assets/js/cta-events.js' ),
			array(),
			wp_get_theme()->get( 'Version' ),
			true
		);
	}
endif;
add_action( 'wp_enqueue_scripts', 'pdforce_enqueue_cta_events' );

if ( ! function_exists( 'pdforce_legacy_news_redirect' ) ) :
	/**
	 * 301s the legacy /news/ paths that Apache cannot reach: the bare /news/
	 * directory (now handled by the WP front controller) and /news/wp-json*
	 * (REST lives at the site root since home moved there). WP-internal
	 * file paths (wp-admin, wp-content, wp-login...) are left alone.
	 *
	 * @since Parent Data Force 1.8
	 *
	 * @return void
	 */
	function pdforce_legacy_news_redirect() {
		$uri = isset( $_SERVER['REQUEST_URI'] ) ? $_SERVER['REQUEST_URI'] : '';
		if ( '' === $uri ) {
			return;
		}
		if ( '/news/' === $uri || '/news' === $uri ) {
			wp_safe_redirect( 'https://www.parentdataforce.com/', 301 );
			exit;
		}
		if ( 0 === strpos( $uri, '/news/wp-json' ) ) {
			wp_safe_redirect( 'https://www.parentdataforce.com' . substr( $uri, strlen( '/news' ) ), 301 );
			exit;
		}
	}
endif;
add_action( 'template_redirect', 'pdforce_legacy_news_redirect' );

if ( ! function_exists( 'pdforce_block_styles' ) ) :
	/**
	 * Registers custom block styles.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_block_styles() {
		register_block_style(
			'core/list',
			array(
				'name'         => 'checkmark-list',
				'label'        => __( 'Checkmark', 'pdforce' ),
				'inline_style' => '
				ul.is-style-checkmark-list {
					list-style-type: "\2713";
				}

				ul.is-style-checkmark-list li {
					padding-inline-start: 1ch;
				}',
			)
		);
	}
endif;
add_action( 'init', 'pdforce_block_styles' );

if ( ! function_exists( 'pdforce_title_figure_pattern' ) ) :
	/**
	 * The single alternation that decides which runs of a post title are data
	 * rather than prose. One left-to-right pass, so a token is never wrapped
	 * twice: SPR26/3331 is taken by the docket branch before the bare-number
	 * branch ever reaches the 26.
	 *
	 * @since Parent Data Force 1.16.0
	 *
	 * @return string
	 */
	function pdforce_title_figure_pattern() {
		// A count is data together with what it counts: "45 Agreements" is one
		// token, not a bare numeral followed by prose. Trailing \b keeps the noun
		// from swallowing a longer word that merely starts the same way.
		$noun = '(?:pages?|records?|agreements?|requests?|emails?|documents?|categories|items?|applicants?|responses?)';
		return '~(?:'
			. '(?:M\.\s*)?G\.L\.\s*c\.\s*\d+[A-Z]*,?\s*§+\s*\d+[A-Z]*(?:\([0-9A-Za-z]+\))*'
			. '|§+\s*\d+[A-Z]*(?:\([0-9A-Za-z]+\))*'
			. '|\d{3}\s*CMR\s*\d+\.\d+(?:\([0-9A-Za-z]+\))*'
			. '|O\.C\.G\.A\.\s*§+\s*[0-9.\-]+'
			. '|SPR\d{2}/\d+'
			. '|\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?'
			. '|\d[\d,]*(?:\.\d+)?\s?%'
			. '|\b\d{1,3}(?:,\d{3})+(?:\s+' . $noun . '\b)?'
			. '|(?<![\d.,$A-Za-z])(?!(?:19|20)\d{2}\b)\d{2,3}(?![\d.,])(?:\s+' . $noun . '\b)?'
			. ')~iu';
	}
endif;

if ( ! function_exists( 'pdforce_title_highlight_meta' ) ) :
	/**
	 * Register the per-post title highlight.
	 *
	 * An article marks one run of its own H1 as the emphasised portion
	 * (`==like this==`). The publisher strips that marker from the stored
	 * title and writes the phrase here instead, so the plain string stays
	 * plain in <title>, REST, search and every card, and the emphasis is
	 * applied only where it is seen: the rendered post-title block.
	 *
	 * @since Parent Data Force 1.17.0
	 */
	function pdforce_title_highlight_meta() {
		register_post_meta(
			'post',
			'_pdforce_title_highlight',
			array(
				'type'         => 'string',
				'single'       => true,
				'show_in_rest' => true,
				'auth_callback' => function ( $allowed, $meta_key, $post_id ) {
					return current_user_can( 'edit_post', $post_id );
				},
			)
		);
	}
endif;
add_action( 'init', 'pdforce_title_highlight_meta' );

if ( ! function_exists( 'pdforce_emphasise_title_text' ) ) :
	/**
	 * Wrap data runs in one text string. A small stop list keeps numerals
	 * that are really prose words ("Chapter 30", "July 30") out of the
	 * emphasis. Months are on the list because a bare day-of-month otherwise
	 * reads as a figure.
	 *
	 * When the post carries an explicit highlight phrase, that phrase is
	 * wrapped whole and the automatic data-run pass is skipped inside it, so
	 * an editorial run like "Waived Its $100 Fee" is one emphasised span
	 * rather than a span nested in a span.
	 *
	 * @since Parent Data Force 1.16.0
	 *
	 * @param string $text      Plain title text, entities intact.
	 * @param string $highlight Phrase to emphasise, or '' for the data-run pass.
	 * @return string
	 */
	function pdforce_emphasise_title_text( $text, $highlight = '' ) {
		if ( '' !== $highlight && '' !== $text ) {
			$needle = html_entity_decode( wp_strip_all_tags( $highlight ), ENT_QUOTES );
			$at     = stripos( $text, $needle );
			if ( false !== $at ) {
				return substr( $text, 0, $at )
					. '<span class="pdf-figure">'
					. substr( $text, $at, strlen( $needle ) )
					. '</span>'
					. substr( $text, $at + strlen( $needle ) );
			}
		}

		$stop = '~\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec|chapter|article|grade|section|part|level|page|appendix|schedule|act)\.?\s*$~i';
		if ( ! preg_match_all( pdforce_title_figure_pattern(), $text, $found,
			PREG_OFFSET_CAPTURE | PREG_SET_ORDER ) ) {
			return $text;
		}
		$out    = '';
		$cursor = 0;
		foreach ( $found as $set ) {
			$token = $set[0][0];
			$at    = $set[0][1];
			$out  .= substr( $text, $cursor, $at - $cursor );
			$before = $at > 0 ? substr( $text, max( 0, $at - 24 ), min( 24, $at ) ) : '';
			$out  .= preg_match( $stop, $before )
				? $token
				: '<span class="pdf-figure">' . $token . '</span>';
			$cursor = $at + strlen( $token );
		}
		return $out . substr( $text, $cursor );
	}
endif;

if ( ! function_exists( 'pdforce_emphasise_post_title' ) ) :
	/**
	 * Emphasis applied to the rendered post-title block, front end only, so
	 * the block editor canvas, the REST payload, the document <title> and the
	 * share URLs all keep the plain string.
	 *
	 * @since Parent Data Force 1.16.0
	 *
	 * @param string         $content       Rendered block HTML.
	 * @param array|null     $parsed_block  Parsed block.
	 * @param WP_Block|null  $instance      Block instance.
	 * @return string
	 */
	function pdforce_emphasise_post_title( $content, $parsed_block = null, $instance = null ) {
		if ( is_admin() || wp_doing_ajax() ) {
			return $content;
		}
		if ( defined( 'REST_REQUEST' ) && REST_REQUEST ) {
			return $content;
		}
		$highlight = (string) get_post_meta( get_the_ID(), '_pdforce_title_highlight', true );
		// Text nodes only: the heading's own tags and any <a> wrapper survive.
		return preg_replace_callback(
			'~(<[^>]+>)((?:(?!<).)+)~s',
			function ( $m ) use ( $highlight ) {
				return $m[1] . pdforce_emphasise_title_text( $m[2], $highlight );
			},
			$content
		);
	}
endif;
add_filter( 'render_block_core/post-title', 'pdforce_emphasise_post_title', 10, 1 );


if ( ! function_exists( 'pdforce_pattern_categories' ) ) :
	/**
	 * Registers pattern categories.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_pattern_categories() {

		register_block_pattern_category(
			'pdforce_page',
			array(
				'label'       => __( 'Pages', 'pdforce' ),
				'description' => __( 'A collection of full page layouts.', 'pdforce' ),
			)
		);

		register_block_pattern_category(
			'pdforce_post-format',
			array(
				'label'       => __( 'Post formats', 'pdforce' ),
				'description' => __( 'A collection of post format patterns.', 'pdforce' ),
			)
		);
	}
endif;
add_action( 'init', 'pdforce_pattern_categories' );

if ( ! function_exists( 'pdforce_register_block_bindings' ) ) :
	/**
	 * Registers the post format block binding source.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return void
	 */
	function pdforce_register_block_bindings() {
		register_block_bindings_source(
			'pdforce/format',
			array(
				'label'              => _x( 'Post format name', 'Label for the block binding placeholder in the editor', 'pdforce' ),
				'get_value_callback' => 'pdforce_format_binding',
			)
		);
	}
endif;
add_action( 'init', 'pdforce_register_block_bindings' );

if ( ! function_exists( 'pdforce_format_binding' ) ) :
	/**
	 * Callback function for the post format name block binding source.
	 *
	 * @since Parent Data Force 1.0
	 *
	 * @return string|void Post format name, or nothing if the format is 'standard'.
	 */
	function pdforce_format_binding() {
		$post_format_slug = get_post_format();

		if ( $post_format_slug && 'standard' !== $post_format_slug ) {
			return get_post_format_string( $post_format_slug );
		}
	}
endif;

if ( ! function_exists( 'pdforce_brand_schema' ) ) :
	/**
	 * Outputs Organization + WebSite JSON-LD on the front page only, so search
	 * engines have an explicit brand logo signal for result presentation.
	 *
	 * The Organization.logo points at the 1024x1024 brand logo (>=112 px, which
	 * is what structured data requires); the 48-multiple favicon guidance is a
	 * separate mechanism (the 432x432 Site Icon).
	 *
	 * @since Parent Data Force 1.0
	 */
	function pdforce_brand_schema() {
		if ( ! is_front_page() ) {
			return;
		}

		$graph = array(
			'@context' => 'https://schema.org',
			'@graph'   => array(
				array(
					'@type' => 'WebSite',
					'@id'   => home_url( '/' ) . '#website',
					'name'  => 'Parent Data Force',
					'url'   => 'https://www.parentdataforce.com/',
				),
				array(
					'@type' => 'Organization',
					'@id'   => home_url( '/' ) . '#organization',
					'name'  => 'Parent Data Force',
					'url'   => 'https://www.parentdataforce.com/',
					'logo'  => array(
						'@type' => 'ImageObject',
						'url'   => 'https://www.parentdataforce.com/news/wp-content/uploads/brand/logo.png',
					),
				),
			),
		);

		echo '<script type="application/ld+json">' . wp_json_encode( $graph ) . "</script>\n";
	}
endif;
add_action( 'wp_head', 'pdforce_brand_schema', 5 );
