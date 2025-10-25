def disable_c_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disable all buttons in the C selection window.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons
    """
    #  Identify all buttons to be disabled in the C selection window
    buttons_to_disable = ['--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
                            '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
                            '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
                            '--button20_top--', '--button20_bottom--']
    control_buttons_to_disable = ['--A--', '--B--']
    selection_windows_to_disable = ['--C1--', '--C2--', '--C3--', '--C4--', '--C5--', '--C6--', '--C7--']
    #  Loop through all buttons to disable them in the C selection window
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)
