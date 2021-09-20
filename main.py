from flask import Flask, request, make_response
from urllib import parse
import requests
import re

app = Flask(__name__)

def fix_html(html_str):
    new_str = re.sub("https:\/\/", "/https://", html_str)
    new_str = re.sub("http:\/\/", "/http://", new_str)
    return new_str

def fetch_url(r):
    if r.encoding and r.encoding.lower() == "utf-8":
        return fix_html(r.text).encode("utf-8")
    else:
        return r.content

@app.route("/<path:url>", methods=["GET", "POST"])
def proxy(url):
    if url.startswith("http://") or url.startswith("https://"):
        new_url = url
    else:
        if request.cookies.get("py_rproxy_url"):
            new_url = request.cookies.get("py_rproxy_url").split(" ")[-1] + "/" + url

    if request.method == "GET":
        req = requests.get(new_url, cookies=request.cookies)
    elif request.method == "POST":
        req = requests.post(new_url, request.form, cookies=request.cookies)

    resp = make_response(fetch_url(req))

    if request.cookies.get("py_rproxy_url"):
        rproxy_urls = request.cookies.get("py_rproxy_url").split()
    else:
        rproxy_urls = []

    i = -1

    while req.status_code != 200 and abs(i) < len(rproxy_urls):
        i = i-1
        new_url = rproxy_urls[i] + "/" + url
        if request.method == "GET":
            req = requests.get(new_url, cookies=request.cookies)
        elif request.method == "POST":
            req = requests.post(new_url, request.form, cookies=request.cookies)

    if url.startswith("http://") or url.startswith("https://"):
        parsed_url = parse.urlparse(req.url)
        rproxy_urls.append(parsed_url.scheme + "://" + parsed_url.netloc)
        resp.set_cookie("py_rproxy_url", " ".join(rproxy_urls))

    resp.headers["Content-Type"] = req.headers["content-type"]
    
    for cookie in req.cookies.keys():
        resp.set_cookie(cookie, req.cookies[cookie])

    return resp

@app.route("/", methods=["GET", "POST"])
def proxy_root():
    return proxy("/")
