# Parent Data Force WordPress Site

This repository contains the source code and deployment tools for the Parent Data Force WordPress site at https://www.parentdataforce.com/wordpress/.

## Structure

- `theme/` - The live WordPress theme (Twenty Twenty-Five customized)
- `tools/` - Scripts for mirroring, fetching, and deploying the site
- `rest/` - WordPress REST API client and utilities
- `docs/` - Documentation and planning
- `captures/` - Snapshots of the live site for verification

## Deployment

1. Theme customizations are made in `theme/twentytwentyfive/`
2. Deploy changes with `tools/upload_theme.py`
3. Mirror the live site with `tools/wp_mirror.py`

## Credentials

Credentials are stored in `rest/credentials.json` (gitignored). Never commit secrets to the repository.

## Security Notes

- Never commit passwords or API keys
- `_setpw.php` requires `WP_NEW_PW` environment variable
- All scripts read credentials from the centralized `credentials.json`