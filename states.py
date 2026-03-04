"""FSM-состояния для калькулятора электромонтажных работ."""

from aiogram.fsm.state import State, StatesGroup


class CalcStates(StatesGroup):
    # Тип объекта
    choose_object_type = State()
    choose_building_type = State()

    # Общие параметры
    enter_area = State()
    enter_rooms = State()
    choose_wall_material = State()

    # Основные электрические точки
    enter_sockets = State()
    enter_switches = State()
    enter_spots = State()
    enter_lamps_simple = State()
    enter_lamps_hard = State()

    # Дополнительные потребители
    enter_stove = State()
    enter_oven = State()
    enter_ac = State()
    enter_boiler = State()
    enter_floor_heating = State()
    enter_washing_machine = State()
    enter_dishwasher = State()

    # Дополнительные работы
    ask_shield = State()
    ask_low_voltage = State()
    ask_demolition = State()
    enter_demolition_count = State()

    # Контакты
    enter_name = State()
    enter_phone = State()
    choose_contact_method = State()

    # Подтверждение
    confirm = State()


class AdminStates(StatesGroup):
    # Управление ценами
    choose_price_item = State()
    enter_new_price = State()

    # Управление коэффициентами
    choose_coeff_item = State()
    enter_new_coeff = State()

    # Разброс
    enter_spread = State()
