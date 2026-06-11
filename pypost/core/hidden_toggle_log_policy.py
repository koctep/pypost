from pypost.core.constants import HIDDEN_MASK


class HiddenToggleLogPolicy:
    """Formats variable key names for env_hidden_flag_changed log events."""

    @staticmethod
    def format_key_name(key: str, *, log_hidden_key_names: bool) -> str:
        if log_hidden_key_names:
            return key
        return HIDDEN_MASK
