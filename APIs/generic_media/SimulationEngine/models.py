from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from enum import Enum
from datetime import datetime, timezone
import uuid

class IntentType(str, Enum):
    ALBUM = "ALBUM"
    ARTIST = "ARTIST"
    GENERIC_MUSIC = "GENERIC_MUSIC"
    GENERIC_PODCAST = "GENERIC_PODCAST"
    GENERIC_MUSIC_NEW = "GENERIC_MUSIC_NEW"
    GENERIC_SOMETHING_ELSE = "GENERIC_SOMETHING_ELSE"
    LIKED_SONGS = "LIKED_SONGS"
    PERSONAL_PLAYLIST = "PERSONAL_PLAYLIST"
    PODCAST_EPISODE = "PODCAST_EPISODE"
    PODCAST_SHOW = "PODCAST_SHOW"
    PUBLIC_PLAYLIST = "PUBLIC_PLAYLIST"
    TRACK = "TRACK"

class FilteringType(str, Enum):
    ALBUM = "ALBUM"
    PLAYLIST = "PLAYLIST"
    TRACK = "TRACK"

class MediaItemMetadata(BaseModel):
    entity_title: Optional[str] = None
    container_title: Optional[str] = None
    description: Optional[str] = None
    artist_name: Optional[str] = None
    content_type: Optional[str] = None

class MediaItem(BaseModel):
    uri: str
    media_item_metadata: MediaItemMetadata
    provider: Optional[str] = None
    action_card_content_passthrough: Optional[str] = None

class Provider(BaseModel):
    name: str
    base_url: str

class Track(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    artist_name: str
    album_id: Optional[str] = None
    rank: int
    release_timestamp: str
    is_liked: bool
    provider: str
    content_type: str = "TRACK"

class Album(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    artist_name: str
    track_ids: List[str]
    provider: str
    content_type: str = "ALBUM"

class Artist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: str
    content_type: str = "ARTIST"

class Playlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    track_ids: List[str]
    is_personal: bool
    provider: str
    content_type: str = "PLAYLIST"

class PodcastEpisode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    show_id: str
    provider: str
    content_type: str = "PODCAST_EPISODE"

class PodcastShow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    episodes: List[PodcastEpisode]
    provider: str
    content_type: str = "PODCAST_SHOW"

class GenericMediaDB(BaseModel):
    providers: List[Provider]
    tracks: List[Track] = []
    albums: List[Album] = []
    artists: List[Artist] = []
    playlists: List[Playlist] = []
    podcasts: List[PodcastShow] = []
    recently_played: List[Dict[str, str]] = []
