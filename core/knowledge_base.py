from skfuzzy import control as ctrl

def get_rules(inputs, outputs):
    #Inputs
    t = inputs['time'] # instant, fast, medium, slow, timeout
    q = inputs['queue'] # empty, small, medium, large, full
    qual = inputs['quality'] # terrible, bad, avg, good, perfect
    conn = inputs['connection'] # lost, unstable, stable
    
    # Outputs
    r_spool = outputs['risk_spooler']
    r_net   = outputs['risk_network']
    r_drv   = outputs['risk_driver']
    r_hard  = outputs['risk_hardware']
    r_twain = outputs['risk_twain']
    r_cable = outputs['risk_cable']

    rules = []

    # =================================================================
    # Block 1: PRINTER
    # =================================================================

    # --- 1. SPOOLER (printer service) ---
    # КРИТИЧНО: Якщо черга велика/повна І час повільний/тайм-аут
    rules.append(ctrl.Rule((q['full'] | q['large']) & (t['timeout'] | t['slow']), r_spool['critical']))
    # СЕРЕДНЬО: Якщо черга середня, а час великий
    rules.append(ctrl.Rule(q['medium'] & (t['timeout'] | t['slow']), r_spool['medium']))
    # НОРМА: Якщо черга мала/пуста АБО час швидкий (Спулер точно ок)
    rules.append(ctrl.Rule(q['empty'] | q['small'] | t['instant'] | t['fast'], r_spool['low']))

    # --- 2. NETWORK ---
    # КРИТИЧНО: Якість ідеальна/добра, АЛЕ час тайм-аут (дані не доходять)
    rules.append(ctrl.Rule((qual['perfect'] | qual['good']) & t['timeout'], r_net['critical']))
    # ВИСОКО: Якість добра, час повільний
    rules.append(ctrl.Rule((qual['perfect'] | qual['good']) & t['slow'], r_net['high']))
    # СЕРЕДНЬО: Якість середня, час повільний
    rules.append(ctrl.Rule(qual['avg'] & (t['slow'] | t['medium']), r_net['medium']))
    # НОРМА: Якщо час швидкий АБО якість погана (якщо якість погана - це не мережа, це драйвер!)
    rules.append(ctrl.Rule(t['instant'] | t['fast'] | qual['terrible'] | qual['bad'], r_net['low']))

    # --- 3. DRIVER ---
    # КРИТИЧНО: Швидко/Миттєво + Жахлива якість (збій кодування)
    rules.append(ctrl.Rule((t['instant'] | t['fast']) & qual['terrible'], r_drv['critical']))
    # ВИСОКО: Швидко + Погана якість
    rules.append(ctrl.Rule((t['instant'] | t['fast']) & qual['bad'], r_drv['high']))
    # СЕРЕДНЬО: Будь-який час + Середня якість (шрифти?)
    rules.append(ctrl.Rule(qual['avg'], r_drv['medium']))
    # НОРМА: Якщо якість добра/ідеальна
    rules.append(ctrl.Rule(qual['good'] | qual['perfect'], r_drv['low']))

    # --- 4. HARDWARE ---
    # КРИТИЧНО: Черга пуста/мала + Жахлива якість (картридж порожній)
    rules.append(ctrl.Rule((q['empty'] | q['small']) & qual['terrible'], r_hard['critical']))
    # ВИСОКО: Черга пуста + Погана якість
    rules.append(ctrl.Rule((q['empty'] | q['small']) & qual['bad'], r_hard['high']))
    # НОРМА: Якщо якість добра
    rules.append(ctrl.Rule(qual['good'] | qual['perfect'], r_hard['low']))

    # =================================================================
    # BLOCK 2: SCANNER
    # =================================================================

    # --- CABLE ---
    rules.append(ctrl.Rule(conn['lost'], r_cable['critical']))
    rules.append(ctrl.Rule(conn['unstable'] & t['timeout'], r_cable['high']))
    rules.append(ctrl.Rule(conn['unstable'] & t['slow'], r_cable['medium']))
    # Якщо зв'язок стабільний - кабель ок
    rules.append(ctrl.Rule(conn['stable'], r_cable['low']))

    # --- TWAIN (DRIVER) ---
    rules.append(ctrl.Rule(conn['stable'] & t['timeout'], r_twain['critical']))
    rules.append(ctrl.Rule(conn['stable'] & t['slow'], r_twain['high']))
    rules.append(ctrl.Rule(conn['stable'] & t['medium'], r_twain['medium']))
    # Якщо швидко - драйвер ок
    rules.append(ctrl.Rule(t['instant'] | t['fast'], r_twain['low']))

    # =========================================
    # BLOCK 3: FALLBACK RULES
    # =========================================
    
    # This rule always works with a small weight. 
    # If a stronger rule (High) works, it will override this one.
    # If no other rule works, this will prevent the system from crashing.
    
    # Logic: If something is good (fast, high quality or stable) -> risks are low
    is_safe = t['instant'] | t['fast'] | q['empty'] | qual['good'] | conn['stable']
    
    rules.append(ctrl.Rule(is_safe, (
        r_spool['negligible'], 
        r_net['negligible'], 
        r_drv['negligible'], 
        r_hard['negligible'],
        r_twain['negligible'],
        r_cable['negligible']
    )))

    return rules