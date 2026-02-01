from PySide6.QtCore import QObject, Signal


class ShardInventory(QObject):
    """
    Centralised shard inventory manager.
    All shard counts live here.
    Any UI can listen to inventory_changed to stay in sync.
    """

    inventory_changed = Signal(dict)

    def __init__(self):
        super().__init__()

        # Core shard values
        self.ancient = 0
        self.void = 0
        self.primal = 0
        self.sacred = 0

    # -----------------------------
    #   INTERNAL UPDATE EMITTER
    # -----------------------------
    def _emit_update(self):
        self.inventory_changed.emit({
            "ancient": self.ancient,
            "void": self.void,
            "primal": self.primal,
            "sacred": self.sacred,
        })

    # -----------------------------
    #   PUBLIC METHODS
    # -----------------------------
    def add(self, shard_type: str):
        """Increment a shard count by name."""
        if hasattr(self, shard_type):
            setattr(self, shard_type, getattr(self, shard_type) + 1)
            self._emit_update()

    def remove(self, shard_type: str):
        """Decrement a shard count safely (never below 0)."""
        if hasattr(self, shard_type):
            current = getattr(self, shard_type)
            setattr(self, shard_type, max(0, current - 1))
            self._emit_update()

    def set_value(self, shard_type: str, value: int):
        """Directly set a shard count."""
        if hasattr(self, shard_type):
            setattr(self, shard_type, max(0, int(value)))
            self._emit_update()

    def reset(self):
        """Reset all shard counts to zero."""
        self.ancient = 0
        self.void = 0
        self.primal = 0
        self.sacred = 0
        self._emit_update()

    # -----------------------------
    #   EXPORT / IMPORT
    # -----------------------------
    def to_dict(self):
        return {
            "ancient": self.ancient,
            "void": self.void,
            "primal": self.primal,
            "sacred": self.sacred,
        }

    def load_from_dict(self, data: dict):
        self.ancient = data.get("ancient", 0)
        self.void = data.get("void", 0)
        self.primal = data.get("primal", 0)
        self.sacred = data.get("sacred", 0)
        self._emit_update()