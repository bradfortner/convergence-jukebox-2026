def disable_b_selection_buttons(jukebox_selection_window, control_button_window):
    """
    Disable all buttons in the B selection window.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        control_button_window: PySimpleGUI window for control buttons
    """
    #  Identify all buttons to be disabled in the B selection window
    buttons_to_disable = ['--button7_top--', '--button7_bottom--', '--button8_top--', '--button8_bottom--',
                          '--button9_top--', '--button9_bottom--', '--button10_top--', '--button10_bottom--',
                          '--button11_top--', '--button11_bottom--', '--button12_top--', '--button12_bottom--',
                          '--button13_top--', '--button13_bottom--']
    control_buttons_to_disable = ['--A--', '--C--']
    selection_windows_to_disable = ['--B1--', '--B2--', '--B3--', '--B4--', '--B5--', '--B6--', '--B7--']
    #  Loop through all buttons to disable them in the B selection window
    for buttons in buttons_to_disable:
        jukebox_selection_window[buttons].update(disabled=True)
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
    for selection_windows in selection_windows_to_disable:
        jukebox_selection_window[selection_windows].update(disabled=True)
