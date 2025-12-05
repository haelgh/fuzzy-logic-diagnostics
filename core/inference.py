from skfuzzy import control as ctrl
# Імпортуємо наші модулі
from core.variables import define_variables
from core.knowledge_base import get_rules

def create_inference_engine():
    """
    Ініціалізація Машини Логічного Висновку.
    Збирає змінні та правила в одну систему управління.
    """
    # 1. Отримуємо змінні (Фазифікація)
    vars_dict = define_variables()
    
    # 2. Отримуємо правила (База Знань)
    rules = get_rules(vars_dict['inputs'], vars_dict['outputs'])
    
    # 3. Створюємо Машину (Control System)
    system_ctrl = ctrl.ControlSystem(rules)
    simulation = ctrl.ControlSystemSimulation(system_ctrl)
    
    # Повертаємо готову симуляцію і самі змінні (для графіків)
    return simulation, vars_dict