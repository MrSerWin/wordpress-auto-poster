#!/usr/bin/env python3
"""
Convenient script to generate and publish articles via Gemini AI
"""
import requests
import json
import sys

def publish_article(topic, seo_focus="", status="draft"):
    """Publish an article to WordPress"""

    url = "http://127.0.0.1:8000/generate"

    payload = {
        "topic": topic,
        "seo_focus": seo_focus if seo_focus else topic,
        "status": status
    }

    print("=" * 80)
    print("WordPress Auto Poster - Article Generator")
    print("=" * 80)
    print(f"Topic: {topic}")
    print(f"SEO Focus: {payload['seo_focus']}")
    print(f"Status: {status}")
    print()
    print("Generating article with Gemini AI...")
    print()

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()

        print("✓ SUCCESS!")
        print("=" * 80)
        print(f"Title: {result.get('title')}")
        print(f"Post ID: {result.get('post_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Link: {result.get('link')}")
        print(f"Featured Image ID: {result.get('featured_image')}")
        print("=" * 80)
        print()

        if status == "draft":
            print("Article saved as DRAFT. Log in to WordPress to review and publish.")
        else:
            print("Article PUBLISHED! Visit the link above to view it.")

        return result

    except requests.exceptions.Timeout:
        print("✗ ERROR: Request timed out. Article generation may take time.")
        print("Try checking the server logs or increasing the timeout.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and publish AI-written articles to WordPress"
    )
    parser.add_argument("topic", help="Article topic/title")
    parser.add_argument("--seo", default="", help="SEO focus keywords")
    parser.add_argument(
        "--status",
        choices=["draft", "publish"],
        default="draft",
        help="Post status (default: draft)"
    )

    args = parser.parse_args()

    publish_article(args.topic, args.seo, args.status)
