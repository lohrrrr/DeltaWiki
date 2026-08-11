# OpenWIKI

OpenWIKI is a lightweight Flask-based wiki engine that renders Markdown files from the `pages/` folder into a navigable web interface.

## Features

- Simple Flask app serving `.md` pages from `pages/`
- Sidebar navigation generated from the directory tree
- Markdown rendering with `markdown2`
- Wiki-style links using `[[Page Name]]` or `[[Page|Label]]`
- Custom category theme support for pages under `pages/<something>/theme.css`

## Project Structure

- `app.py` — main Flask application
- `pages/` — Markdown content source
- `static/` — CSS and JavaScript assets
- `templates/` — Jinja2 HTML templates

## Requirements

- Python 3.8+
- Flask
- markdown2

```bash
python -m pip install flask markdown2
```

## Writing Pages

Place Markdown files under the `pages/` directory.

- `pages/README.md` is the default homepage.
- Additional pages can be nested inside folders.
- Use underscores `_` in filenames for spaces in the menu label.

Example:

- `pages/Getting_Started.md` → displayed as `Getting Started`
- `pages/guides/Install.md` → displayed in the `guides` section

## Wiki Links

Use internal link syntax inside Markdown content:

```md
[[Page Name]]
[[Page_Name|Custom label]]
```

These links resolve to `/page/Page_Name`.

## Custom homepage

The homepage is currently served from `pages/README.md` by the `index()` route in `app.py`.

To change the default page, update `return page_view('README')` in `app.py` and point it to another file base name.

## Community Theme Support

Pages under `pages/<something>/` can include a `theme.css` file.

When present, the wiki will load that CSS for the community page.

## License

See license file.
