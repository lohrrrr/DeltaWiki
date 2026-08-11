Congrats on installing OpenWiki on your server!

This page is the default homepage content for your wiki. You can change this text by editing this file directly:

- `pages/README.md`

## Change the main file

To change the homepage, edit `app.py` and update the default page name in `return page_view('README')` inside the `index()` route. Use the new file base name without the `.md` extension, for example:

- `return page_view('Home')`
- `return page_view('Welcome')`
- `return page_view('Start')`

Then create the corresponding file in `pages/`, such as `pages/Home.md`.

## Need a quick edit?

- Open `pages/README.md`
- Replace the text above with your own welcome message
- Save the file and refresh your wiki in the browser
