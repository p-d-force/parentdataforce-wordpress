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
