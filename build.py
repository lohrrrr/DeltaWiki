import os
import re
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import markdown2

BASE_DIR = Path(__file__).parent
PAGES_DIR = BASE_DIR / "pages"
DIST_DIR = BASE_DIR / "dist"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

def fake_url_for(endpoint, **values):
    if endpoint == "static":
        filename = values.get("filename", "")
        return f"/static/{filename}"
    if endpoint == "community_theme":
        community = values.get("community", "")
        return f"/community_static/{community}/theme.css"
    if endpoint == "page_view":
        subpath = values.get("subpath", "")
        return f"/page/{subpath}"
    return "/"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
env.globals["url_for"] = fake_url_for
template = env.get_template("page.html")

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

def render_page(subpath: str, sidebar_tree: list) -> str:
    file_path = PAGES_DIR / f"{subpath}.md"
    if not file_path.exists() and (PAGES_DIR / subpath).is_dir():
        file_path = PAGES_DIR / subpath / "index.md"

    if not file_path.exists():
        return None

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

    return template.render(
        content=html_content,
        tree=sidebar_tree,
        title=Path(subpath).name.replace("_", " "),
        custom_theme=custom_theme
    )

def main():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, DIST_DIR / "static")

    sidebar_tree = build_tree(PAGES_DIR, PAGES_DIR)

    for theme_file in PAGES_DIR.glob("*/theme.css"):
        community_name = theme_file.parent.name
        dest_dir = DIST_DIR / "community_static" / community_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(theme_file, dest_dir / "theme.css")

    for md_file in PAGES_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(PAGES_DIR).as_posix()
        subpath = str(Path(rel_path).with_suffix(""))

        rendered = render_page(subpath, sidebar_tree)
        if rendered:
            out_file = DIST_DIR / "page" / subpath / "index.html"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(rendered, encoding="utf-8")

    root_html = render_page("README", sidebar_tree) or render_page("index", sidebar_tree)
    if root_html:
        (DIST_DIR / "index.html").write_text(root_html, encoding="utf-8")

if __name__ == "__main__":
    main()
