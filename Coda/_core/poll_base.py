from typing import List
from .constants import PollLayoutStyle


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
