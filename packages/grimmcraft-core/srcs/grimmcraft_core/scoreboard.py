
class ScoreBoard:
    """
    A full scoreboard for integer counters.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self.counters = {}

    def add_score(self, name: str, value: int = 0):
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

    def score_reset(self, name: str):
        if name in self.counters:
            self.counters[name] = 0

    @property
    def score(self, name: str):
        if name not in self.counters:
            return 0
        return self.counters[name]

    @score.setter
    def score(self, name: str, value: int):
        if name not in self.counters.keys():
            self.add_score(name)

        self.counters[name] = value
