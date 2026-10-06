<?php
/**
 * Title: Ways to contribute
 * Slug: pdforce/contribute
 * Categories: pdforce_page
 * Block Types: core/group
 * Description: The full ways-to-help page — six cards, a subscribe link, and
 *              the public-comment guidance block anchored at #public-comment.
 *
 * @package WordPress
 * @subpackage Pdforce
 * @since Parent Data Force 1.14
 */

?>
<!-- wp:group {"className":"pdf-contrib","layout":{"type":"default"}} -->
<div class="wp-block-group pdf-contrib">
	<!-- wp:paragraph {"className":"pdf-kicker"} -->
	<p class="pdf-kicker"><?php esc_html_e( 'Ways to help', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->

	<!-- wp:heading {"level":1,"fontSize":"xx-large"} -->
	<h1 class="has-xx-large-font-size"><?php esc_html_e( 'Six ways to help this work travel further.', 'pdforce' ); ?></h1>
	<!-- /wp:heading -->

	<!-- wp:paragraph {"className":"is-style-text-subtitle"} -->
	<p class="is-style-text-subtitle"><?php esc_html_e( 'Parent Data Force keeps a lot of records requests in flight at once. Money keeps them moving. Documents and testimony keep the record honest. Take whichever of these fits your week.', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->

	<!-- wp:group {"className":"pdf-contrib-grid","layout":{"type":"default"}} -->
	<div class="wp-block-group pdf-contrib-grid">
		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Fund', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Donate', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'One-time or monthly, it pays the copying fees and filing costs that decide whether a district hands over its records or bills you for them.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/donate/"><?php esc_html_e( 'Donate →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Records', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Submit documents and data', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'A settlement agreement, an IEP, a placement decision, a fee letter, minutes from a meeting. Send the document and we will use it in an appeal or publish it in the tracker.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/submit/#upload"><?php esc_html_e( 'Upload documents →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Speak', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Speak at public comment', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'Two minutes on the record at your school committee meeting is public documentation. We will help you write it.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="#public-comment"><?php esc_html_e( 'Prepare your remarks →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Help', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Ask a district question', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'Tell us what your district did and we will tell you what the law gives you, which form to file, and how long the clock has been running.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/submit/#help"><?php esc_html_e( 'Request help →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Account', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Ask privately, in a thread you can see', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'A free member account gives you a private ticket that stays with your question: the document, the correction, and the answer in one place.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/account/register/"><?php esc_html_e( 'Create an account →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->

		<!-- wp:group {"className":"pdf-card pdf-contrib-card","layout":{"type":"default"}} -->
		<div class="wp-block-group pdf-card pdf-contrib-card">
			<!-- wp:paragraph {"className":"pdf-card-tag"} -->
			<p class="pdf-card-tag"><?php esc_html_e( 'Track', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:heading {"level":3,"className":"pdf-card-title"} -->
			<h3 class="pdf-card-title"><?php esc_html_e( 'Request your district', 'pdforce' ); ?></h3>
			<!-- /wp:heading -->
			<!-- wp:paragraph -->
			<p><?php esc_html_e( 'The settlement records project only covers districts we have written to. Ask for yours and we will add it to the request list and the tracker.', 'pdforce' ); ?></p>
			<!-- /wp:paragraph -->
			<!-- wp:buttons -->
			<div class="wp-block-buttons">
				<!-- wp:button {"className":"pdf-contrib-cta"} -->
				<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="mailto:joey@parentdataforce.com?subject=Please%20add%20my%20district%20to%20the%20settlement%20records%20project"><?php esc_html_e( 'Request your district →', 'pdforce' ); ?></a></div>
				<!-- /wp:button -->
			</div>
			<!-- /wp:buttons -->
		</div>
		<!-- /wp:group -->
	</div>
	<!-- /wp:group -->

	<!-- wp:paragraph {"className":"pdf-kicker"} -->
	<p class="pdf-kicker"><?php esc_html_e( 'Stay current', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->

	<!-- wp:paragraph -->
	<p><?php esc_html_e( 'New investigations, settlement records, and appeal decisions as they are filed.', 'pdforce' ); ?></p>
	<!-- /wp:paragraph -->

	<!-- wp:buttons -->
	<div class="wp-block-buttons">
		<!-- wp:button {"className":"pdf-contrib-cta"} -->
		<div class="wp-block-button pdf-contrib-cta"><a class="wp-block-button__link wp-block-button__link--no-border-radius" href="https://www.parentdataforce.com/updates/"><?php esc_html_e( 'Subscribe →', 'pdforce' ); ?></a></div>
		<!-- /wp:button -->
	</div>
	<!-- /wp:buttons -->

	<!-- wp:group {"anchor":"public-comment","id":"public-comment","className":"pdf-guidance","layout":{"type":"default"}} -->
	<div class="wp-block-group pdf-guidance" id="public-comment">
		<!-- wp:heading {"level":2} -->
		<h2 class="wp-block-heading"><?php esc_html_e( 'Prepare your public comment', 'pdforce' ); ?></h2>
		<!-- /wp:heading -->

		<!-- wp:paragraph -->
		<p><?php esc_html_e( 'Two minutes at a school committee meeting is public documentation, and it is the fastest record you can create.', 'pdforce' ); ?></p>
		<!-- /wp:paragraph -->

		<!-- wp:list {"ordered":true} -->
		<ol class="wp-block-list">
			<!-- wp:list-item -->
			<li><strong><?php esc_html_e( 'Find the meeting.', 'pdforce' ); ?></strong> <?php esc_html_e( 'Your school committee posts the agenda and start time on the district website. Public comment is almost always a named agenda item — read it before you go so you know when to sign up.', 'pdforce' ); ?></li>
			<!-- /wp:list-item -->
			<!-- wp:list-item -->
			<li><strong><?php esc_html_e( 'Sign up when you arrive.', 'pdforce' ); ?></strong> <?php esc_html_e( 'Many committees will not call you unless you gave the clerk your name before the item comes up. The rules differ district to district.', 'pdforce' ); ?></li>
			<!-- /wp:list-item -->
			<!-- wp:list-item -->
			<li><strong><?php esc_html_e( 'Two minutes, three parts.', 'pdforce' ); ?></strong> <?php esc_html_e( 'Who you are and which district you are from. What happened, with a date, and the document that proves it if you have one. What you are asking the committee to do about it.', 'pdforce' ); ?></li>
			<!-- /wp:list-item -->
			<!-- wp:list-item -->
			<li><strong><?php esc_html_e( 'Send it to us first.', 'pdforce' ); ?></strong> <?php esc_html_e( 'We will read it with you and tell you which records to put on the table. Email joey@parentdataforce.com with the subject “Help with my public comment”.', 'pdforce' ); ?></li>
			<!-- /wp:list-item -->
		</ol>
		<!-- /wp:list -->

		<!-- wp:paragraph -->
		<p><?php esc_html_e( 'Our own testimony is on the public record here:', 'pdforce' ); ?> <a href="https://www.parentdataforce.com/appearances/"><?php esc_html_e( 'Appearances', 'pdforce' ); ?></a></p>
		<!-- /wp:paragraph -->
	</div>
	<!-- /wp:group -->
</div>
<!-- /wp:group -->