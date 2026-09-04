"""Validation for author-controlled YAML before a build can publish anything."""

from datetime import date

import yaml

from .dates import parse_date


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently replacing earlier values."""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            # SafeLoader handles YAML merges after checking explicit duplicate keys.
            if key_node.tag == "tag:yaml.org,2002:merge":
                key = "<<"
            else:
                key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("YAML mapping keys must be strings")
            if key in keys:
                line = key_node.start_mark.line + 1
                raise ValueError(f"Duplicate YAML key {key!r} at line {line}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def load_yaml_mapping(text: str) -> dict:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected a YAML mapping of field names to values")
    return value


def require_type(value, expected, field: str) -> None:
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        raise ValueError(f"{field} must be a {expected.__name__}")


def validate_metadata(metadata: dict) -> None:
    for field in ("title", "slug", "status", "image"):
        if field in metadata:
            require_type(metadata[field], str, field)
    if metadata.get("description") is not None:
        require_type(metadata["description"], str, "description")
    if "status" in metadata:
        status = metadata["status"].strip().lower()
        if status not in {"published", "draft", "active", "completed", "archived"}:
            raise ValueError("status must be published, draft, active, completed, or archived")
    for field in ("date", "last_updated"):
        if field in metadata:
            value = metadata[field]
            if field == "last_updated" and value is None:
                continue
            if isinstance(value, str):
                try:
                    parse_date(value)
                except ValueError as exc:
                    raise ValueError(f"{field} must be an ISO date or datetime") from exc
            elif not isinstance(value, date):
                raise ValueError(f"{field} must be an ISO date or datetime")
    if metadata.get("tags") is not None:
        require_type(metadata["tags"], list, "tags")
        for tag in metadata["tags"]:
            require_type(tag, str, "tags entry")
    if metadata.get("links") is not None:
        validate_links(metadata["links"], "links")


def validate_links(links, field: str) -> None:
    require_type(links, list, field)
    for link in links:
        require_type(link, dict, f"{field} entry")
        for key in ("label", "url"):
            require_type(link.get(key), str, f"{field}.{key}")
