# facebook-data-parse

Parse Facebook "Posts" export JSON into a smaller, cleaned JSON file using a mapping DSL.

## What it does
- Reads a `profile_posts_*.json` file from a Facebook data export.
- Decodes mojibake text (latin1 → utf-8) and converts timestamps to UTC strings.
- Extracts only the fields defined in `scripts/posts.mapping.json`.
- Writes a sorted output JSON file to `data/output/`.

## Requirements
- Python 3.9+ (no external dependencies)

## Quick start
1. Put your Facebook export under `data/input/` (the default layout from Facebook is fine).
2. Find the posts JSON file (it is usually named like `profile_posts_1.json`).
3. Run the parser:

```bash
python3 scripts/posts.py \
  data/input/<facebook-export>/posts/profile_posts_1.json
```

Output will be written to `data/output/posts_<start>_<end>.json` and the path is printed.

## Options
```bash
python3 scripts/posts.py \
  --mapping scripts/posts.mapping.json \
  --output-dir data/output \
  --sort-field timestamp \
  --sort-order asc \
  --collapse-single-branches \
  --flatten-dicts \
  data/input/<facebook-export>/posts/profile_posts_1.json
```

- `--mapping`: Use a different mapping JSON.
- `--output-dir`: Where to write the processed JSON.
- `--sort-field`: Field name to sort by in the processed output.
- `--sort-order`: `asc` or `desc`.
- `--collapse-single-branches`: Collapses single-item lists recursively in output.
- `--flatten-dicts`: Flattens nested dicts into dotted keys.

## Mapping DSL
The mapping file controls everything that is extracted. See:
- `scripts/posts.mapping.json`
- `scripts/posts.mapping.md`

The mapping supports:
- Dot paths, array traversal with `[]`, and fallback path lists.
- `transform` functions (`decode`, `to_utc`, or custom functions in `posts.py`).
- `each` + `cases` for conditional array emission.

## Notes
- Input JSON must be a list of posts.
- The script prints the output file path on success.
