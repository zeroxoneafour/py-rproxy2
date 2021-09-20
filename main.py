from flask import Flask, request, make_response
from urllib import parse
import requests
import re

# definitions
server_addr = "127.0.0.1"
server_port = "5000"

app = Flask(__name__)

# fix links
def fix_html(html_str):
    new_str = re.sub("https:\/\/", "/https://", html_str)
    new_str = re.sub("http:\/\/", "/http://", new_str)
    return new_str

# get request data
def fetch_url(r):
    if r.encoding and r.encoding.lower() == "utf-8":
        return fix_html(r.text).encode("utf-8")
    else:
        return r.content

# main
@app.route("/<path:url>", methods=["GET", "POST"])
def proxy(url):
    # handle the proxy url cookie
    if request.cookies.get("py_rproxy_url"):
        rproxy_urls = request.cookies.get("py_rproxy_url").split()
    else:
        rproxy_urls = []

    if url.startswith("http://") or url.startswith("https://"):
        new_url = url
        if request.method == "GET":
            req = requests.get(new_url, cookies=request.cookies)
        elif request.method == "POST":
            req = requests.post(new_url, request.form, cookies=request.cookies)
        parsed_url = parse.urlparse(req.url).scheme + "://" + parse.urlparse(req.url).netloc
        if parsed_url in rproxy_urls:
            del rproxy_urls[rproxy_urls.index(parsed_url)]
        rproxy_urls.append(parsed_url)
    else:
        # handle local urls passed to the server
        if request.cookies.get("py_rproxy_url"):
            # indexer
            i = -1
            # check if we can use url per each subdomain
            while True:
                new_url = rproxy_urls[i] + "/" + url
                if request.method == "GET":
                    req = requests.get(new_url, cookies=request.cookies)
                elif request.method == "POST":
                    req = requests.post(new_url, request.form, cookies=request.cookies)
                i = i - 1
                if ( req.status_code>=200 and req.status_code<300 ) or abs(i) >= len(rproxy_urls):
                    break

    resp = make_response(fetch_url(req), req.status_code)

    # auto set cookies
    for cookie in req.cookies.keys():
        resp.set_cookie(cookie, req.cookies[cookie])

    # handle normal urls passed to the server
    resp.set_cookie("py_rproxy_url", " ".join(rproxy_urls))

    # auto set header
    #for header in req.headers.keys():
    #    resp.headers[header] = req.headers[header]

    # fix up some headers I don't want
    #del resp.headers["X-Frame-Options"]
    #resp.headers["Host"] = server_addr + ":" + server_port

    resp.headers["Content-Type"] = req.headers["content-type"]

    return resp

# handle root
@app.route("/", methods=["GET", "POST"])
def proxy_root():
    return proxy("/")

if __name__ == "__main__":
    app.run(host=server_addr, port=server_port, threaded=True)
