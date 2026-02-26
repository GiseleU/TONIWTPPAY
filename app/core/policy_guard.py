# Phase 0 stub for policy checks
# Always returns True for now

class PolicyGuard:
    @staticmethod
    def can_send_message(*args, **kwargs) -> bool:
        return True

    @staticmethod
    def check_consent(*args, **kwargs) -> bool:
        return True

    @staticmethod
    def check_opt_out(*args, **kwargs) -> bool:
        return True