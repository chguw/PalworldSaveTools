"""Pure-Python services operating on the decoded save dict.

None of these import Qt. ``save_service`` wraps the installed ``palsav`` engine;
``world_service`` queries the dumped dict directly; ``data_service`` serves
static game-data / i18n JSON from the main project resources.
"""
