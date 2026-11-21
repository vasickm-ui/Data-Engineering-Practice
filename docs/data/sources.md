# Data Sources

## Bluesky Jetstream

- **Endpoint:** `wss://jetstream2.us-east.bsky.network/subscribe`
- **Type:** public WebSocket stream, real-time JSON events, no API keys required
- **Content:** posts, likes, reposts, follows and blocks from the Bluesky social network
- **Filtering:** the `wantedCollections` query parameter selects event types (e.g. `app.bsky.feed.post`)

## `ingestion/bluesky_stream.py`

Connects to Jetstream, receives a set number of events (posts only by default, all types with `--all`), prints a short summary of each one and saves the raw messages to a JSONL file in `samples/`.

```
python ingestion/bluesky_stream.py --limit 200
```
