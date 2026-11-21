"""
Bluesky Jetstream - real-time data research (phase I).

Connects to the public Jetstream WebSocket (no keys required), receives events
and prints a short overview. Stores raw messages in a JSONL file for analysis.

Running:
    python ingestion/bluesky_stream.py                 # 50 messages, posts only
    python ingestion/bluesky_stream.py --limit 200
    python ingestion/bluesky_stream.py --all           # all event types (likes, follows, ...)
"""

import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

import websockets

JETSTREAM_URL = "wss://jetstream2.us-east.bsky.network/subscribe"
DEFAULT_COLLECTIONS = ["app.bsky.feed.post"]


def build_url(collections):
    if not collections:
        return JETSTREAM_URL
    query = "&".join(f"wantedCollections={c}" for c in collections)
    return f"{JETSTREAM_URL}?{query}"


def summarize(event):
    """A short, readable description of a single event."""
    kind = event.get("kind")
    if kind != "commit":
        return f"[{kind}] did={event.get('did')}"

    commit = event["commit"]
    collection = commit.get("collection")
    op = commit.get("operation")
    record = commit.get("record") or {}

    if collection == "app.bsky.feed.post" and op == "create":
        text = record.get("text", "").replace("\n", " ")[:100]
        langs = ",".join(record.get("langs", []) or [])
        return f"[post] ({langs}) {text}"
    return f"[{collection}] {op}"


async def stream(limit, collections, out_path):
    url = build_url(collections)
    print(f"Connecting to: {url}\n")

    counts = Counter()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    async with websockets.connect(url) as ws:
        with out_path.open("w", encoding="utf-8") as f:
            for _ in range(limit):
                raw = await ws.recv(decode=True)
                event = json.loads(raw)
                f.write(raw + "\n")

                commit = event.get("commit", {})
                counts[(event.get("kind"), commit.get("collection"), commit.get("operation"))] += 1
                print(summarize(event))

    print(f"\nSaved {limit} messages to {out_path}")
    print("\nOverview by type (kind, collection, operation):")
    for key, n in counts.most_common():
        print(f"  {n:4d}  {key}")


def main():
    parser = argparse.ArgumentParser(description="Bluesky Jetstream explorer")
    parser.add_argument("--limit", type=int, default=50, help="number of messages to receive")
    parser.add_argument("--all", action="store_true", help="all event types, not just posts")
    parser.add_argument("--out", default="samples/bluesky_sample.jsonl", help="output JSONL file")
    args = parser.parse_args()

    collections = [] if args.all else DEFAULT_COLLECTIONS
    asyncio.run(stream(args.limit, collections, Path(args.out)))


if __name__ == "__main__":
    main()