from pathlib import Path

from docutils.core import publish_parts
from dotenv import load_dotenv
from github import Github
from markdown import Markdown
from mkdocs.structure.pages import *
from rubberdoc.doc_handler import MaterialMKDocsHandler, RubberDocConfig

load_dotenv()

EXTENSIONS = [
        'admonition', 
        'pymdownx.snippets', 
        'pymdownx.superfences', 
        'attr_list', 
        'pymdownx.highlight', 
        'pymdownx.inlinehilite', 
        'tables', 
        'toc', 
        'pymdownx.tabbed', 
        'pymdownx.details', 
        'pymdownx.tasklist',
        'pymdownx.keys'
]

VALID_FILE_FORMATS = ['.py', '.md', '.rst', '.txt']

class CustomDocHandler(MaterialMKDocsHandler):
    """Override Material styled DocHandler from Rubberdoc.

    Allow more fine-tuned control over the generation of 
    each node processed.
    """
    def process_node(self, level, node, parent=None):
        if parent:
            self.doc.append(self.wrap_func_cls_lbl(parent.name))
        
        # function or class name
        self.doc.append(self.wrap_func_cls_name(level, node))
        
        docstring = self.wrap_parsed_docstring(
            self.get_parsed_docstring(node))
        self.doc.append(self.wrap_docstring(docstring))
        
        if self.config.output['include_source_code']:
            source_code = self.get_node_code(node)
            self.doc.append(self.wrap_codeblock(source_code))

class Nav:
    def __init__(self):
        self.title: str = str()
        self.path: str = str()
        self.children: list = list()


class GithubSite:
    """ Collects data about a github repo and provides various views """
    def __init__(self, owner, repo, token=None):
        self.gh = self.__setup_github_api(token)
        if owner and repo:
            self.repository = self.gh.get_repo(f"{owner}/{repo}")
        self.md = Markdown(extensions=EXTENSIONS)
        self.owner = owner 
        self.repo = repo

    def __setup_github_api(self, token):
        if token:
            return Github(token, per_page=50)
        else:
            return Github(
                os.getenv("GITHUB_CLIENT_ID"), 
                os.getenv("GITHUB_CLIENT_SECRET"),
                per_page=50)

    def get_nav(self):
        tree = self.repository.get_git_tree(
            self.repository.default_branch, recursive=True)
        nav = list()
        for path in tree.tree:
            p = path.path
            if p.startswith('tests'):
                continue
            if any([p.endswith(i) for i in VALID_FILE_FORMATS]):
                nav.append(p)
        return self.get_path_dict(nav)
    
    def get_page(self, path):
        return self.repository.get_contents(
            path).decoded_content.decode('utf-8')
    
    def markdown_to_html(self, mkdn_content):
        return self.md.convert(mkdn_content)

    def rst_to_html(self, content):
        return publish_parts(
                content, 
                writer_name='html5_polyglot', 
                settings_overrides={'output_encoding': 'unicode'})['html_body']
    
    def get_converted_content(self, path):
        content = self.get_page(path)
        if path.endswith('.md'):
            return self.markdown_to_html(content)
        elif path.endswith('.py'):
            return self.py_to_html(content)
        elif path.endswith('.rst') or path.endswith('.txt'):
            return self.rst_to_html(content)
        else:
            return content
    
    def py_to_html(self, content):
        rd = CustomDocHandler(
            file_or_path=content, 
            config=RubberDocConfig())
        return self.markdown_to_html(rd.process())
    
    def get_path_dict(self, paths: list[str or Path]) -> dict:
        """Builds a tree like structure out of a list of paths"""
        def _recurse(dic: dict, chain: tuple[str, ...] or list[str], path):
            if not isinstance(dic, dict):
                return
            if len(chain) == 0:
                return
            if len(chain) == 1:
                dic[chain[0].split('.')[0]] = path
                return
            key, *new_chain = chain
            if key not in dic:
                dic[key] = {}
            _recurse(dic[key], new_chain, path)
            return

        new_path_dict = {}
        for path in paths:
            _recurse(new_path_dict, Path(path).parts, path)
        return new_path_dict

    def get_toc(self):
        toc = self.md.toc 
        if len(toc.splitlines()) == 3:
            return None 
        return toc

    def search(self, term):
        return self.build_search_html(
            self.gh.search_code(
                query=term, 
                repo=f"{self.owner}/{self.repo}"))
    
    def build_search_html(self, results):
        html_builder = '<div class="search_results">'
        for res in results:
            result_html = '<div class="result">'
            result_html += f"<a href='/{self.owner}/{self.repo}/{res.path}'>{res.name}</a>" 
            result_html += "</div>"
            html_builder += result_html
        html_builder += '</div>'
        return html_builder
    
    def search_repo(self, term):
        return self.build_repo_search_html(
            self.gh.search_repositories(term))
    
    def build_repo_search_html(self, results):
        html_builder = '<div class="search_results thin-scrollbar">'
        for i, res in enumerate(results):
            if i == 29: break
            # if res.language == 'Python':
            result_html = f'<a class="result" href="/{res.full_name}">'
            result_html += f"<b>{res.full_name}</b><br>" 
            result_html += f"<p>{res.description}</p>"
            result_html += "</a>"
            # res.topics: list
            # res.stargazers_count
            # res.subscribers_count
            # res.watchers_count
            html_builder += result_html
        html_builder += '</div>'
        return html_builder
    