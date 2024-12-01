from iamai.engine import Engine


class Plugin:
    def register_rules(self, engine: Engine) -> None:
        raise NotImplementedError("Plugins must implement the register_rules method.")
