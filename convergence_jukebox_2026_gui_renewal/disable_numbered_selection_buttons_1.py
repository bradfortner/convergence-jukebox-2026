def disable_numbered_selection_buttons(control_button_window):
    """
    Disable all buttons for the numbered selection window.

    Disables buttons 1-7 (seven numbered control buttons).
    Uses dynamic range-based generation instead of hardcoded button lists.

    Args:
        control_button_window: The control buttons PySimpleGUI window object

    Returns:
        None
    """
    # Dynamically generate button keys for buttons 1-7
    control_buttons_to_disable = [f'--{i}--' for i in range(1, 8)]

    # Disable all numbered control buttons
    for control_button_key in control_buttons_to_disable:
        control_button_window[control_button_key].update(disabled=True)
