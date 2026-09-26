<?php
/**
 * Title: Share this article
 * Slug: pdforce/share-buttons
 * Inserter: no
 * Description: Social share row for single posts (X, Facebook, LinkedIn, Bluesky, email, copy link).
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.6
 */

if ( ! is_singular( 'post' ) ) {
	return;
}

$pdforce_share_url   = rawurlencode( get_permalink() );
$pdforce_share_title = rawurlencode( get_the_title() );
?>
<!-- wp:html -->
<div class="pdf-share">
	<span class="pdf-share-label"><?php esc_html_e( 'Share', 'pdforce' ); ?></span>
	<a class="pdf-share-link" href="https://twitter.com/intent/tweet?text=<?php echo esc_attr( $pdforce_share_title ); ?>&url=<?php echo esc_attr( $pdforce_share_url ); ?>" target="_blank" rel="noopener nofollow" aria-label="<?php esc_attr_e( 'Share on X', 'pdforce' ); ?>">X</a>
	<a class="pdf-share-link" href="https://www.facebook.com/sharer/sharer.php?u=<?php echo esc_attr( $pdforce_share_url ); ?>" target="_blank" rel="noopener nofollow" aria-label="<?php esc_attr_e( 'Share on Facebook', 'pdforce' ); ?>">Facebook</a>
	<a class="pdf-share-link" href="https://www.linkedin.com/sharing/share-offsite/?url=<?php echo esc_attr( $pdforce_share_url ); ?>" target="_blank" rel="noopener nofollow" aria-label="<?php esc_attr_e( 'Share on LinkedIn', 'pdforce' ); ?>">LinkedIn</a>
	<a class="pdf-share-link" href="https://bsky.app/intent/compose?text=<?php echo esc_attr( rawurlencode( get_the_title() . ' ' . get_permalink() ) ); ?>" target="_blank" rel="noopener nofollow" aria-label="<?php esc_attr_e( 'Share on Bluesky', 'pdforce' ); ?>">Bluesky</a>
	<a class="pdf-share-link" href="mailto:?subject=<?php echo esc_attr( $pdforce_share_title ); ?>&body=<?php echo esc_attr( rawurlencode( get_the_title() . ' — ' . get_permalink() ) ); ?>" aria-label="<?php esc_attr_e( 'Share by email', 'pdforce' ); ?>">Email</a>
	<button type="button" class="pdf-share-link pdf-share-copy" data-share-url="<?php echo esc_url( get_permalink() ); ?>"><?php esc_html_e( 'Copy link', 'pdforce' ); ?></button>
</div>
<!-- /wp:html -->
