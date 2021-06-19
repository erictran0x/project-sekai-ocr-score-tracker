from abc import abstractmethod


class State:

    def __init__(self, i):
        self.id = i

    @abstractmethod
    def update(self, storage):
        pass

    def log(self, s):
        print(f'[State{self.id}] {s}')

    def __eq__(self, other):
        return isinstance(other, State) and self.id == other.id
