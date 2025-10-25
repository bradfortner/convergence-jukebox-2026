def enable_all_buttons(jukebox_selection_window, control_button_window):
    """
    Enable all song buttons, control buttons, and selection windows.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons
    """
    buttons_to_enable = ['--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
                            '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
                            '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
                            '--button6_top--', '--button6_bottom--', '--button7_top--', '--button7_bottom--',
                            '--button8_top--', '--button8_bottom--', '--button9_top--', '--button9_bottom--',
                            '--button10_top--', '--button10_bottom--', '--button11_top--', '--button11_bottom--',
                            '--button12_top--', '--button12_bottom--', '--button13_top--', '--button13_bottom--',
                            '--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
                            '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
                            '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
                            '--button20_top--', '--button20_bottom--']
    control_buttons_to_enable = ['--A--', '--B--', '--C--']
    selection_windows_to_enable = ['--A1--', '--A2--', '--A3--', '--A4--', '--A5--', '--A6--', '--A7--',
                                    '--B1--', '--B2--', '--B3--', '--B4--', '--B5--', '--B6--', '--B7--',
                                    '--C1--', '--C2--', '--C3--', '--C4--', '--C5--', '--C6--', '--C7--']
    for buttons in buttons_to_enable:
        jukebox_selection_window[buttons].update(disabled=False)
    for control_buttons in control_buttons_to_enable:
        control_button_window[control_buttons].update(disabled=False)
    for selection_windows in selection_windows_to_enable:
        jukebox_selection_window[selection_windows].update(disabled=False)
