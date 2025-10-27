def disable_a_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disable all buttons in the A selection window.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons
    """
    #  Identify all buttons to be disabled in the A selection window
    buttons_to_disable = ['--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
                          '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
                          '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
                          '--button6_top--', '--button6_bottom--']
    control_buttons_to_disable = ['--B--', '--C--']
    selection_windows_to_disable = ['--A1--', '--A2--', '--A3--', '--A4--', '--A5--', '--A6--', '--A7--']
    #  Loop through all buttons to disable them in the A selection window
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)
