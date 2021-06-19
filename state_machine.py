from states.state_0_teamselect import TeamSelect
from states.state_1_ingame import InGame
from states.state_2_liveresult import LiveResult


class StateMachine:

    _TEAMSELECT = TeamSelect()
    _INGAME = InGame()
    _LIVERESULT = LiveResult()

    def __init__(self):
        self.state = StateMachine._TEAMSELECT
        self.storage = {}

    def update(self):
        trans, self.storage, direction = self.state.update(self.storage)
        if trans:
            if direction:
                self.next()
            else:
                self.prev()

    def prev(self):
        if self.state == StateMachine._INGAME:
            self.state = StateMachine._TEAMSELECT
        self.log(f'Heading to prev state {self.state.id}')

    def next(self):
        if self.state == StateMachine._TEAMSELECT:
            self.state = StateMachine._INGAME
        elif self.state == StateMachine._INGAME:
            self.state = StateMachine._LIVERESULT
        elif self.state == StateMachine._LIVERESULT:
            self.state = StateMachine._TEAMSELECT
        self.log(f'Heading to next state {self.state.id}')

    @staticmethod
    def log(s):
        print(f'[StateMachine] {s}')
