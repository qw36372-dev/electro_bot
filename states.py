"""FSM-состояния для калькулятора электромонтажных работ."""

from aiogram.fsm.state import State, StatesGroup


class CalcStates(StatesGroup):
    # Геолокация
    enter_city = State()
    enter_district = State()

    # Тип объекта
    choose_object_type = State()
    choose_building_type = State()

    # Доп. работы на участке (только для дома)
    ask_outdoor_work = State()
    choose_outdoor_types = State()

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
    enter_floor_heating = State()
    enter_washing_machine = State()
    enter_dishwasher = State()

    # Блок да/нет
    enter_boiler = State()
    ask_shield = State()
    ask_low_voltage = State()
    ask_demolition = State()
    enter_demolition_count = State()

    # Доп. сведения мастеру
    enter_extra_info = State()

    # Контакты
    enter_name = State()
    enter_phone = State()
    choose_contact_method = State()

    # Подтверждение
    confirm = State()


class AdminStates(StatesGroup):
    choose_price_item = State()
    enter_new_price = State()
    choose_coeff_item = State()
    enter_new_coeff = State()
    enter_spread = State()
