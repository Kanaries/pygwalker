class GlobalVarManager:
    """A class to manage global variables."""
    global_gid = 0

    @classmethod
    def get_global_gid(cls) -> int:
        return_gid = cls.global_gid
        cls.global_gid += 1
        return return_gid
