from typing import Any, Dict, Optional
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


class PollMedia:
    text: str
    emoji: Optional[Any]


class PollAnswers:
    text: str
    emoji: Optional[Any]


class PollAnswerCount:
    id: int
    count: int
    me_voted: bool


class PollResults:
    is_finalized: bool
    answer_counts: PollAnswerCount


class Poll(ObjectBuilder):
    """
    Represents a Discord Poll object
    """

    question: str
    answers: PollAnswers
    expiry: str
    allow_multiselect: bool
    layout_type: PollLayoutStyle
    results: PollResults
