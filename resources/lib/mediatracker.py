import urllib.request
import urllib.parse
import json
from typing import TypedDict, Literal

class ExternalId(TypedDict):
    imdbId: str
    tmdbId: int

class ProgressPayload(TypedDict):
    mediaType: Literal["movie", "tv"]
    id: ExternalId
    seasonNumber: int
    episodeNumber: int
    action: Literal["playing", "paused"]
    progress: float
    duration: float

class MarkAsSeenPayload(TypedDict):
    mediaType: Literal["movie", "tv"]
    id: ExternalId
    seasonNumber: int
    episodeNumber: int
    duration: float

class MediaTracker:
    def __init__(self, url: str, apiToken: str) -> None:
        self.url = url
        self.apiToken = apiToken

    def setProgress(self, payload: ProgressPayload):
        url = urllib.parse.urljoin(
            self.url, '/api/progress/by-external-id?token=' + self.apiToken)

        putJson(url, payload)

    def markAsSeen(self, payload: MarkAsSeenPayload):
        url = urllib.parse.urljoin(
            self.url, '/api/seen/by-external-id?token=' + self.apiToken)

        putJson(url, payload)


def putJson(url: str, data: dict):
    postdata = json.dumps(data).encode()

    headers = {"Content-Type": "application/json; charset=UTF-8"}

    httprequest = urllib.request.Request(
        url,
        data=postdata,
        headers=headers,
        method="PUT")

    response = urllib.request.urlopen(httprequest)
