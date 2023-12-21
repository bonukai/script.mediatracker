import xbmc
import xbmcaddon
import xbmcgui
import json
from resources.lib.mediatracker import MediaTracker
from resources.lib.previous_action import PreviousActions

class Scrobbler:
    def __init__(self) -> None:
        self.previousActions = PreviousActions()
        self.__addon__ = xbmcaddon.Addon()

    def scrobble(self, player: xbmc.Player):
        if player.isPlaying() == False:
            return

        playingItem = player.getPlayingItem()

        if not isinstance(playingItem, xbmcgui.ListItem):
            return

        videoInfoTag = playingItem.getVideoInfoTag()

        if not isinstance(videoInfoTag, xbmc.InfoTagVideo):
            return

        id = videoInfoTag.getDbId()

        apiToken = self.__addon__.getSettingString('apiToken')
        mediatrackerUrl = self.__addon__.getSettingString('mediatrackerUrl')

        if len(apiToken) == 0:
            xbmc.log("MediaTracker: missing api token", xbmc.LOGDEBUG)
            return

        if len(mediatrackerUrl) == 0:
            xbmc.log("MediaTracker: missing MediaTracker url", xbmc.LOGDEBUG)
            return

        mediaTracker = MediaTracker(mediatrackerUrl, apiToken)

        duration = videoInfoTag.getDuration()
        currentTime = player.getTime()
        progress = currentTime / duration

        if videoInfoTag.getMediaType() == "episode":
            res = kodiJsonRequest('VideoLibrary.GetEpisodeDetails', {
                'episodeid': videoInfoTag.getDbId(),
                'properties': ['tvshowid']
            })

            tvShowId = res.get("episodedetails", {}).get("tvshowid")

            if tvShowId == None:
                xbmc.log("MediaTracker: missing tvShowId for episode " +
                         videoInfoTag.getTitle(), xbmc.LOGDEBUG)
                return

            res = kodiJsonRequest('VideoLibrary.GetTVShowDetails', {
                'tvshowid': tvShowId,
                'properties': ['uniqueid']
            })

            tmdbId = res.get("tvshowdetails", {}).get(
                "uniqueid", {}).get("tmdb") or None
            imdbId = res.get("tvshowdetails", {}).get(
                "uniqueid", {}).get("imdb") or None

            if tmdbId == None and imdbId == None:
                xbmc.log(
                    f"MediaTracker: missing tmdbId and imdbId for episode of \"{videoInfoTag.getTVShowTitle()}\"", xbmc.LOGERROR)
                return

            seasonNumber = videoInfoTag.getSeason()
            episodeNumber = videoInfoTag.getEpisode()

            xbmc.log(
                f"MediaTracker: updating progress for tv show \"{videoInfoTag.getTVShowTitle()}\" {seasonNumber}x{episodeNumber} - {progress * 100:.2f}%", xbmc.LOGDEBUG)

            mediaTracker.setProgress({
                "mediaType": "tv",
                "id": {
                    "imdbId": imdbId,
                    "tmdbId": tmdbId
                },
                "seasonNumber": seasonNumber,
                "episodeNumber": episodeNumber,
                "progress": progress,
                "duration": duration * 1000,
            })

            if self.previousActions.canMarkAsSeen(id, progress):
                xbmc.log(
                    f"MediaTracker: marking tv show \"{videoInfoTag.getTVShowTitle()}\" {seasonNumber}x{episodeNumber} as seen", xbmc.LOGDEBUG)

                mediaTracker.markAsSeen({
                    "mediaType": "tv",
                    "id": {
                        "imdbId": imdbId,
                        "tmdbId": tmdbId
                    },
                    "seasonNumber": seasonNumber,
                    "episodeNumber": episodeNumber,
                    "duration": duration * 1000,
                })

        elif videoInfoTag.getMediaType() == "movie":
            tmdbId = videoInfoTag.getUniqueID('tmdbId') or None
            imdbId = videoInfoTag.getUniqueID('imdb') or None
            
            if tmdbId == None and imdbId == None:
                xbmc.log(
                    f"MediaTracker: missing tmdbId and imdbId for \"{videoInfoTag.getTitle()}\"", xbmc.LOGERROR)
                return

            xbmc.log(
                f"MediaTracker: updating progress for movie \"{videoInfoTag.getTitle()}\" - {progress * 100:.2f}%", xbmc.LOGDEBUG)

            mediaTracker.setProgress({
                "mediaType": "movie",
                "id": {
                    "imdbId": imdbId,
                    "tmdbId": tmdbId
                },
                "progress": progress,
                "duration": duration * 1000,
            })

            if self.previousActions.canMarkAsSeen(id, progress):
                xbmc.log(
                    f"MediaTracker: marking movie \"{videoInfoTag.getTitle()}\" as seen", xbmc.LOGDEBUG)

                mediaTracker.markAsSeen({
                    "mediaType": "movie",
                    "id": {
                        "imdbId": imdbId,
                        "tmdbId": tmdbId
                    },
                    "duration": duration * 1000,
                })


def kodiJsonRequest(method: str, params: dict):
    args = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    }
    request = xbmc.executeJSONRPC(json.dumps(args))
    response = json.loads(request)

    if not isinstance(response, dict):
        return {}

    return response.get('result', {})
