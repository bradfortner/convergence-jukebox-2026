import sys


def the_bands_name_check(jukebox_selection_window, dir_path):
    """
    Add "The " prefix to band names that appear in the_bands.txt file,
    excluding bands listed in the_exempted_bands.txt.

    Args:
        jukebox_selection_window: PySimpleGUI window for song selection
        dir_path: Directory path for accessing band name files
    """
    # Add The to bands with The in their names
    # Open and read the_bands.txt file
    jukebox_selection_windows_to_update = ['--button0_bottom--', '--button1_bottom--', '--button2_bottom--', '--button3_bottom--',
                '--button4_bottom--', '--button5_bottom--', '--button6_bottom--', '--button7_bottom--', '--button8_bottom--',
                '--button9_bottom--', '--button10_bottom--', '--button11_bottom--', '--button12_bottom--', '--button13_bottom--',
                '--button14_bottom--', '--button15_bottom--', '--button16_bottom--', '--button17_bottom--', '--button18_bottom--',
                '--button19_bottom--', '--button20_bottom--']

    def band_names_exemptions(the_band_to_update, band_to_check, file_path):
        """
        Check if band name should be exempted from 'The' prefix.

        Args:
            the_band_to_update: Band name with 'The' prefix
            band_to_check: Original band name
            file_path: Path to exemptions file

        Returns:
            str: Band name (either with 'The' or original)
        """
        # Open and read the_exempted_bands.txt file as list exempted_bands from The
        with open(file_path, 'r') as file:
            # Read each line in the file and strip newline characters
            exempted_bands = [line.strip() for line in file]
        if the_band_to_update in exempted_bands:
            the_band_to_update = band_to_check
        return the_band_to_update

    if sys.platform.startswith('linux'):
        bands_file_path = dir_path + '/the_bands.txt'
        exemptions_file_path = dir_path + '/the_exempted_bands.txt'

        for jukebox_selection_windows in jukebox_selection_windows_to_update:
            with open(bands_file_path, 'r') as the_bands_text_file:
                the_bands = the_bands_text_file.read()

                # Get text of band to check
                band_to_check = jukebox_selection_window[jukebox_selection_windows].get_text()
                # check if a band is present in a file
                if band_to_check.lower() in the_bands:
                    # Add The to bands name
                    # Band name exemptions
                    the_band_to_update = 'The ' + band_to_check
                    the_band_to_update = band_names_exemptions(the_band_to_update, band_to_check, exemptions_file_path)
                    print(the_band_to_update)
                    # Check if band name is too long
                    if len(the_band_to_update) > 22:
                        jukebox_selection_window[jukebox_selection_windows].Widget.config(font='Helvetica 10 bold')
                    else:
                        # Update Jukebox selection button
                        jukebox_selection_window[jukebox_selection_windows].update(the_band_to_update)

    if sys.platform.startswith('win32'):
        bands_file_path = dir_path + '\\the_bands.txt'
        exemptions_file_path = dir_path + '\\the_exempted_bands.txt'

        for jukebox_selection_windows in jukebox_selection_windows_to_update:
            with open(bands_file_path, 'r') as the_bands_text_file:
                the_bands = the_bands_text_file.read()

                # Get text of band to check
                band_to_check = jukebox_selection_window[jukebox_selection_windows].get_text()
                # check if a band is present in a file
                if band_to_check.lower() in the_bands:
                    # Add The to bands name
                    # Band name exemptions
                    the_band_to_update = 'The ' + band_to_check
                    the_band_to_update = band_names_exemptions(the_band_to_update, band_to_check, exemptions_file_path)
                    print(the_band_to_update)
                    # Check if band name is too long
                    if len(the_band_to_update) > 22:
                        jukebox_selection_window[jukebox_selection_windows].Widget.config(font='Helvetica 10 bold')
                    else:
                        # Update Jukebox selection button
                        jukebox_selection_window[jukebox_selection_windows].update(the_band_to_update)
