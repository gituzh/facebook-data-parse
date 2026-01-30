# Mapping DSL for posts.py

Format: JSON (for the mapping) + Markdown (for this description).

## Overview
The mapping file controls the entire transform. The script reads the JSON mapping
and builds the output without any hard-coded field list.

Top-level shape:
```
{
  "fields": { "<output_field>": <field_spec>, ... }
}
```

## Field spec
Each output field has a spec that tells the extractor what to read and how to
transform it.

Common keys:
- `path` (string or list of strings): Where to read the value from.
- `transform` (string or list): Transform(s) to apply in order.
- `first` (bool): When `path` yields multiple values, return the first non-empty
  value instead of a list.
- `collapse_single` (bool, default true): If a `path` yields exactly one value,
  return the single value rather than a list.

### path syntax
- Dot-separated keys: `data.post`
- Array traversal: `attachments[]` means “iterate each item.”
- Combined: `attachments[].data[].media.uri`
- Fallback path list: `["data[].post", "data[].title"]` tries each and returns
  the first non-empty match.

### transform
- A transform is a function name (string).
- If the name is not in the registry, the script tries a function with the same
  name in the module (auto-resolve).
- Examples: `decode`, `to_utc`

## Arrays with `each` and `cases`
Use `each` when the field itself should be an array of transformed items.

Example shape:
```
"attachments": {
  "path": "attachments[]",
  "each": {
    "cases": [
      {
        "when": "data[].media",
        "emit": {
          "media.uri": { "path": "data[].media.uri", "transform": "decode" }
        }
      }
    ]
  }
}
```

Keys:
- `path`: selects the array to iterate.
- `each.cases[]`: list of conditional mappings.
- `when`: path that decides if the case applies for that item.
- `emit`: mapping of output keys to field specs.

### emit keys
`emit` keys can be dotted (e.g., `media.uri`) to produce nested output objects.

## Defaults and behavior
- Missing `transform`: value is copied as-is.
- `collapse_single` is true unless explicitly set to false.
- `first` overrides `collapse_single` by selecting the first non-empty value.
- `--collapse-single-branches` collapses any single-item list recursively in output.
- `--flatten-dicts` flattens nested dicts into dotted keys (global).

## Built-in transforms (current)
- `decode`: fixes mojibake (latin1 -> utf-8)
- `to_utc`: converts epoch seconds to `YYYYMMDD_hhmmss` in UTC
