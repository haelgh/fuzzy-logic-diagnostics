import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def define_variables():
    # === INPUTS ===
    time = ctrl.Antecedent(np.arange(0, 121, 1), 'time')
    queue = ctrl.Antecedent(np.arange(0, 51, 1), 'queue')
    quality = ctrl.Antecedent(np.arange(0, 11, 1), 'quality')
    connection = ctrl.Antecedent(np.arange(0, 101, 1), 'connection')

    # --- TIME ---
    time['instant'] = fuzz.trimf(time.universe, [0, 0, 15])
    time['fast']    = fuzz.trimf(time.universe, [10, 25, 40])
    time['medium']  = fuzz.trimf(time.universe, [30, 50, 70])
    time['slow']    = fuzz.trimf(time.universe, [60, 80, 100])
    time['timeout'] = fuzz.trapmf(time.universe, [90, 110, 120, 120])

    # --- QUEUE ---
    queue['empty']  = fuzz.trimf(queue.universe, [0, 0, 5])
    queue['small']  = fuzz.trimf(queue.universe, [3, 7, 12])
    queue['medium'] = fuzz.trimf(queue.universe, [10, 20, 30])
    queue['large']  = fuzz.trimf(queue.universe, [25, 35, 45])
    queue['full']   = fuzz.trapmf(queue.universe, [40, 48, 50, 50])

    # --- QUALITY ---
    quality['terrible'] = fuzz.trapmf(quality.universe, [0, 0, 2, 4])
    quality['bad']      = fuzz.trimf(quality.universe, [2, 4, 6])
    quality['avg']      = fuzz.trimf(quality.universe, [4, 6, 8])
    quality['good']     = fuzz.trimf(quality.universe, [6, 8, 9])
    quality['perfect']  = fuzz.trapmf(quality.universe, [8, 9, 10, 10])

    # --- ЗВ'ЯЗОК ---
    connection['lost']     = fuzz.zmf(connection.universe, 0, 20)
    connection['unstable'] = fuzz.trimf(connection.universe, [15, 50, 85])
    connection['stable']   = fuzz.smf(connection.universe, 80, 100)

    # === OUTPUTS ===
    r_spooler = ctrl.Consequent(np.arange(0, 101, 1), 'risk_spooler')
    r_net     = ctrl.Consequent(np.arange(0, 101, 1), 'risk_network')
    r_driver  = ctrl.Consequent(np.arange(0, 101, 1), 'risk_driver')
    r_hard    = ctrl.Consequent(np.arange(0, 101, 1), 'risk_hardware')
    r_twain   = ctrl.Consequent(np.arange(0, 101, 1), 'risk_twain')
    r_cable   = ctrl.Consequent(np.arange(0, 101, 1), 'risk_cable')

    # DEFASIFICATION
    risk_names = ['negligible', 'low', 'medium', 'high', 'critical']
    for r in [r_spooler, r_net, r_driver, r_hard, r_twain, r_cable]:
        r.automf(5, names=risk_names)

    return {
        "inputs": {"time": time, "queue": queue, "quality": quality, "connection": connection},
        "outputs": {
            "risk_spooler": r_spooler, "risk_network": r_net, 
            "risk_driver": r_driver, "risk_hardware": r_hard,
            "risk_twain": r_twain, "risk_cable": r_cable
        }
    }