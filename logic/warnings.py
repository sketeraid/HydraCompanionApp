from PySide6.QtWidgets import QMessageBox

# Highest rarity per shard
HIGHEST_RARITY = {
    "Ancient": "Legendary",
    "Void": "Legendary",
    "Primal": "Mythical",
    "Sacred": "Legendary"
}

def check_hard_pity_and_chance(shard_name, current_pity, hard_pity, current_chance):
    """
    shard_name: str        -> "Ancient", "Void", "Primal", "Sacred"
    current_pity: int      -> current pity count
    hard_pity: int         -> hard pity threshold for highest rarity
    current_chance: float  -> current % chance for highest rarity
    """

    highest_rarity = HIGHEST_RARITY.get(shard_name, "Unknown")

    # Condition 1: Exceeded hard pity
    if current_pity > hard_pity:
        show_warning_popup(
            title="Incorrect Pull Tracking Detected",
            message=(
                f"Hello User!\n\n"
                f"You have surpassed the Hard Pity Level for {highest_rarity} "
                f"on the {shard_name} shard.\n\n"
                f"This indicates that the correct number of pulls has not been accurately recorded."
            )
        )
        return

    # Condition 2: Chance exceeded 100%
    if current_chance > 100:
        show_warning_popup(
            title="Incorrect Pull Tracking Detected",
            message=(
                f"Hello User!\n\n"
                f"Your {highest_rarity} chance for the {shard_name} shard has exceeded 100%.\n\n"
                f"This indicates that the correct number of pulls has not been accurately recorded."
            )
        )
        return


def show_warning_popup(title, message):
    popup = QMessageBox()
    popup.setIcon(QMessageBox.Warning)
    popup.setWindowTitle(title)
    popup.setText(message)
    popup.exec()