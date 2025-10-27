def create_font_size_window_updates():
    """
    Generate the list of all button element keys for font size updates.

    Creates a list of 42 keys representing the 21 song selection buttons (0-20),
    each with '_top' (song title) and '_bottom' (artist) variants. This dynamic
    generation replaces the need for manually listing all keys.

    Returns:
        list: Keys for all button elements in the format '--buttonN_[top|bottom]--'
              where N ranges from 0 to 20.

    Example:
        >>> keys = create_font_size_window_updates()
        >>> len(keys)
        42
        >>> keys[0]
        '--button0_top--'
        >>> keys[1]
        '--button0_bottom--'
    """
    return [f'--button{i}_{suffix}--' for i in range(21) for suffix in ['top', 'bottom']]
