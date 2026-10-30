import os
import re
import shutil
import unicodedata
from html.parser import HTMLParser
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
        return f"/static/{values.get('filename', '')}"
    if endpoint == "community_theme":
        return f"/community_static/{values.get('community', '')}/theme.css"
    if endpoint == "page_view":
        return f"/page/{values.get('subpath', '')}"
    return "/"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
env.globals["url_for"] = fake_url_for
template = env.get_template("page.html")

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", text).strip("-")

def build_tree(dir_path: Path, base_path: Path):
    tree = []
    if not dir_path.exists():
        return tree

    items = sorted(os.listdir(dir_path))
    folders = [i for i in items if (dir_path / i).is_dir()]
    files = [i for i in items if i.endswith(".md")]

    for folder in folders:
        sub_tree = build_tree(dir_path / folder, base_path)
        tree.append({
            "type": "folder",
            "name": folder.replace("_", " "),
            "children": sub_tree
        })

    for file in files:
        rel_path = (dir_path / file).relative_to(base_path).as_posix()
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

        target = target.strip()
        label = label.strip()

        # Обработка внутристраничных якорей вида [[#Раздел]] или [[#Раздел|Текст]]
        if target.startswith("#"):
            anchor = slugify(target.lstrip("#"))
            return f'<a href="#{anchor}">{label}</a>'

        # Ссылка с якорем на другую страницу вида [[Page#Раздел]]
        if "#" in target:
            page, anchor = target.split("#", 1)
            page_slug = page.strip().replace(" ", "_")
            anchor_slug = slugify(anchor)
            return f'<a href="/page/{page_slug}#{anchor_slug}">{label}</a>'

        target_slug = target.replace(" ", "_")
        return f'<a href="/page/{target_slug}">{label}</a>'

    return re.sub(pattern, replace, html_content)

def inject_header_anchors(html_content: str) -> str:
    header_pattern = re.compile(r"<h([1-6])(.*?)>(.*?)</h\1>", re.DOTALL)

    def replace(match):
        level, attrs, title = match.groups()
        clean_title = re.sub(r"<[^>]+>", "", title)
        anchor_id = slugify(clean_title)
        clean_attrs = re.sub(r'\s*id="[^"]*"', "", attrs)
        return f'<h{level} id="{anchor_id}"{clean_attrs}>{title}</h{level}>'

    return header_pattern.sub(replace, html_content)

class PageMetadataParser(HTMLParser):
    BLOCK_TAGS = {"br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "p", "tr"}

    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.description_parts = []
        self.in_first_h1 = False
        self.found_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag == "h1" and not self.found_h1:
            self.found_h1 = True
            self.in_first_h1 = True
        elif tag in self.BLOCK_TAGS and not self.in_first_h1:
            self.description_parts.append(" ")

    def handle_endtag(self, tag):
        if tag == "h1" and self.in_first_h1:
            self.in_first_h1 = False
        elif tag in self.BLOCK_TAGS and not self.in_first_h1:
            self.description_parts.append(" ")

    def handle_data(self, data):
        if self.in_first_h1:
            self.title_parts.append(data)
        else:
            self.description_parts.append(data)

    @staticmethod
    def normalized_text(parts):
        return " ".join("".join(parts).split())

def extract_page_metadata(html_content: str, fallback_title: str):
    parser = PageMetadataParser()
    parser.feed(html_content)
    title = parser.normalized_text(parser.title_parts) or fallback_title
    description = parser.normalized_text(parser.description_parts)[:100].strip()
    return title, description

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
        extras=["fenced-code-blocks", "tables", "strike", "task_lists"]
    )
    html_content = inject_header_anchors(html_content)
    html_content = parse_wiki_links(html_content)
    page_title, description = extract_page_metadata(
        html_content,
        Path(subpath).name.replace("_", " ")
    )

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
        page_title=page_title,
        description=description,
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
