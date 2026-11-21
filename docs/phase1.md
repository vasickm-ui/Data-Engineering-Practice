# Phase I - Data Source Access

## Access

- **Source:** Bluesky Jetstream (see [data/sources.md](data/sources.md))
- **Registration / keys:** not required, the stream is public
- **Streaming check:** WebSocket connection to `wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post` (Postman → New → WebSocket)
- **Python check:** `ingestion/bluesky_stream.py`, using the `websockets` library

## Event envelope

Every message shares the same top-level structure:

| Attribute | Description |
|---|---|
| `did` | ID of the user who made the change |
| `time_us` | event time in microseconds (Unix) |
| `cursor` | stream position, used for reconnecting |
| `kind` | `commit` (data change), `identity` or `account` |
| `commit.operation` | `create`, `update` or `delete` |
| `commit.collection` | entity type (see below) |
| `commit.rkey` | record key within the user's repository |
| `commit.record` | entity data, missing for `delete` |
| `commit.cid` | content hash of the record |

## Entities

| Collection | Entity | Key `record` attributes |
|---|---|---|
| `app.bsky.feed.post` | post | `text`, `createdAt`, `langs`, `reply.parent/root`, `embed` (images, links, quoted posts) |
| `app.bsky.feed.like` | like | `subject.uri` (liked post), `createdAt`, `via` (when liked through a repost) |
| `app.bsky.feed.repost` | repost | `subject.uri` (reposted post), `createdAt` |
| `app.bsky.graph.follow` | follow | `subject` (followed user's DID), `createdAt` |
| `app.bsky.graph.block` | block | `subject` (blocked user's DID), `createdAt` |
| `app.bsky.graph.listitem` | list membership | `list`, `subject`, `createdAt` |

Other applications built on the same network also appear in the stream (e.g. `fm.teal.feed.play`, music plays). They are not Bluesky entities and can be filtered out with `wantedCollections`.

## Observations

- In an unfiltered sample of 100 events, likes were the most common Bluesky event and posts only ~3%, so filtering by collection matters.
- `createdAt` formats are inconsistent (with and without milliseconds, `Z` or `+00:00`) and must be normalized during processing.
- Post `text` can be empty (image-only posts) and `langs` can be missing.
