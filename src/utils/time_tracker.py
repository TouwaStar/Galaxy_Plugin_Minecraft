from galaxyutils.time_tracker import TimeTracker as OGTimeTracker


class TimeTracker(OGTimeTracker):
    def get_tracking_games(self):
        return [game_id for game_id in self._running_games_dict]


from galaxyutils.time_tracker import (  # noqa: ignore F401
    GameNotTrackedException,
    GamesStillBeingTrackedException,
)
