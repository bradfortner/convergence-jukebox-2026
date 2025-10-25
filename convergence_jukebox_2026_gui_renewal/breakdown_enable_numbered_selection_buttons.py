def enable_numbered_selection_buttons(control_button_window):
    """
    Enable all numbered selection buttons (1-7).

    Args:
        control_button_window: PySimpleGUI window for control buttons
    """
    buttons_to_enable = ['--1--', '--2--', '--3--', '--4--', '--5--', '--6--', '--7--']
    for buttons in buttons_to_enable:
        control_button_window[buttons].update(disabled=False)
