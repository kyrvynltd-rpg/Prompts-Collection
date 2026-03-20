# Landing Page for Social Previews

This folder contains a tiny branded redirect landing page with Open Graph and Twitter metadata.

## Why this exists

Streamlit deployments on Render have limited control over rich link previews in messaging tools. A static landing page can provide explicit metadata so shared links display your chosen name, description, and logo.

## Recommended use

1. Host this folder as a static page (for example with GitHub Pages or a Render Static Site).
2. Share the landing URL publicly.
3. Keep the redirect target set to your Streamlit app URL.

Current redirect target:

- [https://prompt-learning-platform.onrender.com/](https://prompt-learning-platform.onrender.com/)

## Note on social images

Some social platforms do not render SVG images for cards. If that happens, replace the og:image and twitter:image URLs in index.html with a hosted PNG or JPG image (recommended size 1200x630).
