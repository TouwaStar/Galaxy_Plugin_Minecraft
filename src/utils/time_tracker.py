from galaxyutils import time_tracker as og_time_tracker


class TimeTracker(og_time_tracker.TimeTracker):
    def get_tracking_games(self):
        return [game_info.game_id for game_info in self._running_games_dict]


from og_time_tracker import (  # noqa: ignore F401
    GameNotTrackedException,
    GamesStillBeingTrackedException,
)
