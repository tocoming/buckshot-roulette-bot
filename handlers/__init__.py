from .start import router as start_router
from .reset import router as reset_router
from .game_setup import router as game_setup_router
from .game_tracking import router as game_tracking_router
from .phone_predictions import router as phone_predictions_router
from .cancel import router as cancel_router
from .language import router as language_router  

def register_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(reset_router)
    dp.include_router(game_setup_router)
    dp.include_router(game_tracking_router)
    dp.include_router(phone_predictions_router)
    dp.include_router(cancel_router)
    dp.include_router(language_router)  
