from flask import render_template, jsonify, Response, url_for, request
from app.routes import bp_main

@bp_main.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@bp_main.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@bp_main.route("/faq", methods=["GET"])
def faq():
    return render_template("faq.html")

@bp_main.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html")

@bp_main.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html")

@bp_main.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Data Quality Checker",
        "version": "1.0.0"
    }), 200

@bp_main.route("/robots.txt", methods=["GET"])
def robots_txt():
    base_url = request.url_root.rstrip("/")
    content = f"""User-agent: *
Allow: /
Allow: /about
Allow: /faq
Allow: /privacy
Allow: /terms
Disallow: /upload
Disallow: /results/
Disallow: /clean/
Disallow: /download/
Disallow: /analyze/
Disallow: /validate-rules/
Disallow: /reset/

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content, mimetype="text/plain")

@bp_main.route("/sitemap.xml", methods=["GET"])
def sitemap_xml():
    base_url = request.url_root.rstrip("/")
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/about</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/faq</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base_url}/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
"""
    return Response(xml_content, mimetype="application/xml")
