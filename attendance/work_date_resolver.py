from datetime import timedelta


class WorkDateResolver:
    @staticmethod
    def resolve(recognized_at, shift):
        if not shift.cross_day:
            return recognized_at.date()

        if recognized_at.time() < shift.end_time:
            return (
                recognized_at
                - timedelta(days=1)
            ).date()

        return recognized_at.date()