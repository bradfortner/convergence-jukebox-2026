def selection_entry_complete(selection_entry_letter, selection_entry_number, jukebox_selection_window,
                            control_button_window, disable_a_selection_buttons,
                            disable_b_selection_buttons, disable_c_selection_buttons,
                            disable_numbered_selection_buttons):
    """
    Complete the selection entry process by disabling all buttons and enabling only
    the selected entry and its corresponding song button.

    Disables all A, B, and C selection buttons plus numbered buttons, then enables only
    the specified selection entry and its associated song button. Uses a mapping dictionary
    instead of 21 hardcoded if statements.

    Args:
        selection_entry_letter: The letter portion of the selection (A, B, or C)
        selection_entry_number: The number portion of the selection (1-7)
        jukebox_selection_window: The jukebox selection PySimpleGUI window object
        control_button_window: The control buttons PySimpleGUI window object
        disable_a_selection_buttons: Function to disable A selection buttons
        disable_b_selection_buttons: Function to disable B selection buttons
        disable_c_selection_buttons: Function to disable C selection buttons
        disable_numbered_selection_buttons: Function to disable numbered buttons

    Returns:
        The completed selection entry string (e.g., "A1", "B5", "C7")
    """
    if selection_entry_number:
        selection_entry = selection_entry_letter + selection_entry_number

    # Disable all selection buttons
    disable_a_selection_buttons()
    disable_b_selection_buttons()
    disable_c_selection_buttons()
    disable_numbered_selection_buttons()

    # Mapping of letters to starting button indices
    letter_to_button_base = {'A': 0, 'B': 7, 'C': 14}

    # Calculate the button index for the selected entry
    if selection_entry_letter in letter_to_button_base and selection_entry_number:
        button_index = letter_to_button_base[selection_entry_letter] + int(selection_entry_number) - 1

        # Enable the selected entry field and its corresponding song buttons
        jukebox_selection_window[f'--{selection_entry_letter}{selection_entry_number}--'].update(disabled=False)
        jukebox_selection_window[f'--button{button_index}_top--'].update(disabled=False)
        jukebox_selection_window[f'--button{button_index}_bottom--'].update(disabled=False)

    # Enable the select button
    control_button_window['--select--'].update(disabled=False)

    return selection_entry
