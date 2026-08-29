"""Check every demo link in data/exercises.json is still live.

YouTube's oEmbed endpoint returns 200 with the title and channel for a public
video, and 4xx for one that is deleted, private or age-gated. Link rot is the
main way a curated video list quietly stops being useful, so run this
occasionally:

    python3 scripts/verify_videos.py
"""
import json, os, sys, urllib.request, urllib.error, urllib.parse

PATH = os.path.join(os.path.dirname(__file__), "..", "data", "exercises.json")


def check(video_id):
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode({
        "url": "https://www.youtube.com/watch?v=" + video_id, "format": "json"})
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            d = json.load(r)
            return True, d.get("author_name", "?"), d.get("title", "?")
    except urllib.error.HTTPError as e:
        return False, "HTTP %s" % e.code, ""
    except Exception as e:
        return False, type(e).__name__, str(e)


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    ex = data["exercises"]
    missing, dead, ok = [], [], 0

    for key, e in ex.items():
        v = e.get("video")
        if not v or not v.get("id"):
            missing.append(e["name"])
            continue
        live, who, title = check(v["id"])
        if live:
            ok += 1
            if v.get("channel") and v["channel"] != who:
                print("  channel changed for %s: %r -> %r" % (e["name"], v["channel"], who))
        else:
            dead.append((e["name"], v["id"], who))

    print("%d live, %d dead, %d without a video (of %d)" % (ok, len(dead), len(missing), len(ex)))
    for name, vid, why in dead:
        print("  DEAD  %-38s %s  (%s)" % (name, vid, why))
    if missing:
        print("\nNo video yet:")
        for n in missing:
            print("  - " + n)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
