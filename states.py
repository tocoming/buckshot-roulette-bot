from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    GameSetup = State()
    GameTracking = State()
    PredictingShot = State()
