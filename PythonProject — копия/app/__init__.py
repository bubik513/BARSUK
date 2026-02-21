from .start import register_start_handlers
from .main_menu import register_main_menu_handlers
from .request import register_requests_handlers

def setup_handlers(dp):
    """
    Регистрация всех хендлеров для бота.
    """
    register_start_handlers(dp)
    register_main_menu_handlers(dp)
    register_requests_handlers((dp))