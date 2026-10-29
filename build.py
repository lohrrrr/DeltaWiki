import os
import re
from pathlib import Path
from flask import Flask, render_template, abort, send_from_directory
import markdown2

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
PAGES_DIR = BASE_DIR / "pages"

def build_tree(dir_path: Path, base_path: Path):
    tree = []
    if not dir_path.exists():
        return tree

    items = sorted(os.listdir(dir_path))
    folders = [i for i in items if (dir_path / i).is_dir()]
    files = [i for i in items if i.endswith(".md")]

    for folder in folders:
        folder_full_path = dir_path / folder
        sub_tree = build_tree(folder_full_path, base_path)
        tree.append({
            "type": "folder",
            "name": folder.replace("_", " "),
            "children": sub_tree
        })

    for file in files:
        file_full_path = dir_path / file
        rel_path = file_full_path.relative_to(base_path).as_posix()
        url_path = str(Path(rel_path).with_suffix(""))
        
        tree.append({
            "type": "file",
            "name": file.replace(".md", "").replace("_", " "),
            "url": f"/page/{url_path}"
        })

    return tree

def parse_wiki_links(html_content: str) -> str:
    pattern = r"\[\[(.*?)\]\]"
    def replace(match):
        val = match.group(1)
        if "|" in val:
            target, label = val.split("|", 1)
        else:
            target, label = val, val
        target = target.strip().replace(" ", "_")
        return f'<a href="/page/{target}">{label.strip()}</a>'
    return re.sub(pattern, replace, html_content)

@app.route('/')
def index():
    return page_view('README')

@app.route('/page/<path:subpath>')
def page_view(subpath):
    file_path = PAGES_DIR / f"{subpath}.md"
    
    if not file_path.exists() and (PAGES_DIR / subpath).is_dir():
        file_path = PAGES_DIR / subpath / "index.md"

    if not file_path.exists():
        abort(404)

    with open(file_path, "r", encoding="utf-8") as f:
        raw_md = f.read()

    html_content = markdown2.markdown(
        raw_md, 
        extras=["fenced-code-blocks", "tables", "header-ids", "strike", "task_lists"]
    )
    html_content = parse_wiki_links(html_content)

    rel_parts = Path(subpath).parts
    custom_theme = None
    if len(rel_parts) >= 1:
        community_name = rel_parts[0]
        theme_path = PAGES_DIR / community_name / "theme.css"
        if theme_path.exists():
            custom_theme = f"/community_static/{community_name}/theme.css"

    sidebar_tree = build_tree(PAGES_DIR, PAGES_DIR)

    return render_template(
        "page.html",
        content=html_content,
        tree=sidebar_tree,
        title=Path(subpath).name.replace("_", " "),
        custom_theme=custom_theme
    )

@app.route('/community_static/<community>/theme.css')
def community_theme(community):
    community_dir = PAGES_DIR / community
    if (community_dir / "theme.css").exists():
        return send_from_directory(community_dir, "theme.css")
    abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)