from collections import deque


class RecognitionStabilizer:
    def __init__(
        self,
        window_size=5,
        required_hits=3
    ):
        if required_hits > window_size:
            raise ValueError(
                "required_hits cannot exceed window_size"
            )

        self.window_size = window_size
        self.required_hits = required_hits
        self.history = deque(
            maxlen=window_size
        )

    def update(self, employee_code):
        self.history.append(employee_code)

        if employee_code is None:
            return None

        hits = sum(
            value == employee_code
            for value in self.history
        )

        if hits >= self.required_hits:
            return employee_code

        return None

    def reset(self):
        self.history.clear()