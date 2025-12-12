from enum import Enum


class embed_base:
    def __init__(
        self,
        title: str,
        description: str,
        color=None,
        image: str = None,
        timestamp=None,
    ) -> None:
        self.tree = {
            "title": title,
            "description": description,
            "color": color.value if isinstance(color, Enum) else color or None,
            "image": {"url": image},
            "fields": [],
        }
        if timestamp:
            self.embed_tree["timestamp"] = timestamp

    async def add_field(self, name: str, value: str, inline: bool):
        self.embed_tree["fields"].append(
            {"name": name, "value": value, "inline": inline}
        )
