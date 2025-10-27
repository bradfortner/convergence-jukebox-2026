def disable_numbered_selection_buttons(control_button_window):
    """
    Disable all numbered selection buttons (1-7).

    Args:
        control_button_window: PySimpleGUI window for control buttons
    """
    #  Identify all buttons to be disabled in the numbered selection window
    control_buttons_to_disable = ['--1--', '--2--', '--3--', '--4--', '--5--', '--6--', '--7--']
    #  Loop through all buttons to disable them in the numbered selection window
    for control_buttons in control_buttons_to_disable:
        control_button_window[control_buttons].update(disabled=True)
