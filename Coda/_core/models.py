from enum import Enum
from typing import Any, Dict, List, Optional
from .constants import PollLayoutStyle


class ObjectBuilder:
    """
    A utility class that converts dictionaries into objects with dot-notation access.
    Automatically recurses into nested dictionaries.
    """

    def __init__(self, data: Dict[str, Any]):
        self.update(data)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the object attributes from a dictionary.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ObjectBuilder(value))
            else:
                setattr(self, key, value)

    def __repr__(self):
        return f"<ObjectBuilder {self.__dict__}>"


class Embed:
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


class PollMediaObject:
    text: str
    emoji: Optional[Any]


class PollAnswersObject:
    text: str
    emoji: Optional[Any]


class PollAnswerCountObject:
    id: int
    count: int
    me_voted: bool


class PollResultsObject:
    is_finalized: bool
    answer_counts: PollAnswerCountObject


class PollObject(ObjectBuilder):
    """
    Represents a Discord Poll object
    """

    question: str
    answers: PollAnswersObject
    expiry: str
    allow_multiselect: bool
    layout_type: PollLayoutStyle
    results: PollResultsObject


class Poll:
    def __init__(
        self,
        text: str,
        answers: List[str],
        duration: int,
        allow_multiselect: bool,
        layout_type: PollLayoutStyle = PollLayoutStyle.DEFAULT,
    ) -> None:
        question = {
            "text": text[:300],
        }
        poll_answers = [
            {"answer_id": i + 1, "poll_media": {"text": answer[:55]}}
            for i, answer in enumerate(answers)
        ]
        self.poll_tree = {
            "question": question,
            "answers": poll_answers,
            "duration": int(duration),
            "allow_multiselect": allow_multiselect,
            "layout_type": layout_type.value,
        }
