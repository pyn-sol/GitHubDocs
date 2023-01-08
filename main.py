import os 

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests

from driver import GithubSite
from template_helpers import Jinja2TemplatesCustom

load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
ACCESS_TOKEN_KEY = 'acto'
THEME = 'gitmock'

app = FastAPI()
templates = Jinja2TemplatesCustom(directory="")

app.mount(
    f"/{THEME}/assets", 
    StaticFiles(directory=f"{THEME}/assets"), 
    name="assets")


def login_or_token(request: Request):
    """
    Check if the user has an access token in their cookies, and if not,
    authenticate the user and return an access token.
    
    Args:
        request (Request): The request object to check for an access token.
    
    Returns:
        str: The access token for the user.
    """
    user_token = request.cookies.get(ACCESS_TOKEN_KEY)
    if not user_token:
        authenticate()
    return user_token


def authenticate():
    # can we pass any extra data here to redirect where they were trying to go?
    return RedirectResponse(f'https://github.com/login/oauth/authorize?client_id={CLIENT_ID}')


@app.get('/')
def no_owner_repo(request: Request):
    user_token = login_or_token(request)
    if not user_token:
        return authenticate()
    return templates.TemplateResponse(
        f'{THEME}/no_owner_repo.html',
        context={
            'request': request, 
            'search_content': ''})


@app.post('/githubdocs_repo_search')
def repo_search(request: Request, q: str = Form()):
    gh = GithubSite(None, None)
    return templates.TemplateResponse(
        f'{THEME}/no_owner_repo.html',
        context={
            'request': request, 
            'search_content': gh.search_repo(term=q)})


@app.post('/{owner}/{repo}/githubdocs_search')
def search(request: Request, owner: str, repo: str, q: str = Form()):
    user_token = login_or_token(request)
    gh = GithubSite(owner, repo, user_token)
    return templates.TemplateResponse(
        f'{THEME}/index.html',
        context={'request': request, 
                 'owner': owner,
                 'repo': repo,
                 'nav': gh.get_nav(), 
                 'content': gh.search(term=q)})


@app.get('/{owner}/{repo}/{path:path}')
def index(request: Request, owner: str, repo: str, path: str):
    user_token = login_or_token(request)      
    gh = GithubSite(owner, repo, user_token)

    if not path:
        path = 'README.md'
    try:
        content = gh.get_converted_content(path)
    except:
        content = gh.get_converted_content(
            path.replace('.md', '.rst'))
    
    return templates.TemplateResponse(
        f'{THEME}/index.html',
        context={'request': request, 
                 'owner': owner,
                 'repo': repo,
                 'nav': gh.get_nav(), 
                 'content': content,
                 'toc': gh.get_toc(),
                 'rate_limit': gh.gh.rate_limiting})

@app.get('/authorize')
def authorize(request: Request, code: str):
    resp = requests.post('https://github.com/login/oauth/access_token', 
        headers={'Accept': 'application/json'}, 
        params={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code
    }).json()

    response = RedirectResponse(url=f"/", status_code=303)
    response.set_cookie(ACCESS_TOKEN_KEY, resp['access_token'])
    return response

