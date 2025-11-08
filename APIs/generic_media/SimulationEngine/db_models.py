import datetime as dt

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, model_validator
from enum import Enum

# Base Model

class GenericMediaBaseModel(BaseModel):
    """Base model for all generic media models."""
    __abstract__ = True
    id: str = Field(
        ...,
        description="Unique identifier for the model.",
        min_length=1,
        max_length=100,
    )

# ---------------------------
# Enum Types
# ---------------------------

class IntentType(str, Enum):
    """Type of search/play intent"""
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
    """Type of content filtering"""
    ALBUM = "ALBUM"
    PLAYLIST = "PLAYLIST"
    TRACK = "TRACK"

class ContentType(str, Enum):
    """Type of media content"""
    TRACK = "TRACK"
    ALBUM = "ALBUM"
    ARTIST = "ARTIST"
    PLAYLIST = "PLAYLIST"
    PODCAST_EPISODE = "PODCAST_EPISODE"
    PODCAST_SHOW = "PODCAST_SHOW"

class ActionType(str, Enum):
    """Type of action performed on media"""
    PLAY = "play"
    SEARCH = "search"

# ---------------------------
# Internal Storage Models
# ---------------------------

class Provider(BaseModel):
    """
    Internal storage model for media providers.
    
    Represents a music/podcast streaming service provider.
    """
    name: str = Field(
        ...,
        description="The name of the media provider (e.g., 'Apple Music', 'Spotify').",
        min_length=1,
        max_length=100
    )
    base_url: HttpUrl = Field(
        ...,
        description="The base URL of the provider's service."
    )

class Track(GenericMediaBaseModel):
    """
    Internal storage model for music tracks.
    
    Represents a single music track/song.
    """
    title: str = Field(
        ...,
        description="The title of the track.",
        min_length=1,
        max_length=500
    )
    artist_name: str = Field(
        ...,
        description="The name of the artist who performed the track.",
        min_length=1,
        max_length=200
    )
    album_id: Optional[str] = Field(
        default=None,
        description="The ID of the album this track belongs to.",
        max_length=100
    )
    rank: int = Field(
        ...,
        description="The popularity rank of the track.",
        ge=1
    )
    release_timestamp: dt.datetime = Field(
        ...,
        description="The release date and time in ISO 8601 format."
    )
    is_liked: bool = Field(
        default=False,
        description="Whether the track is marked as liked by the user."
    )
    provider: str = Field(
        ...,
        description="The media provider for this track.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="TRACK",
        description="The type of content (always 'TRACK' for tracks)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'TRACK' for track objects."""
        if self.content_type != ContentType.TRACK:
            raise ValueError("content_type must be 'TRACK' for Track objects")
        return self

class Album(GenericMediaBaseModel):
    """
    Internal storage model for music albums.
    
    Represents a music album containing multiple tracks.
    """
    title: str = Field(
        ...,
        description="The title of the album.",
        min_length=1,
        max_length=500
    )
    artist_name: str = Field(
        ...,
        description="The name of the artist who created the album.",
        min_length=1,
        max_length=200
    )
    track_ids: List[str] = Field(
        default_factory=list,
        description="List of track IDs included in this album."
    )
    provider: str = Field(
        ...,
        description="The media provider for this album.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="ALBUM",
        description="The type of content (always 'ALBUM' for albums)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'ALBUM' for album objects."""
        if self.content_type != ContentType.ALBUM:
            raise ValueError("content_type must be 'ALBUM' for Album objects")
        return self

class Artist(GenericMediaBaseModel):
    """
    Internal storage model for music artists.
    
    Represents a music artist or band.
    """
    name: str = Field(
        ...,
        description="The name of the artist or band.",
        min_length=1,
        max_length=200
    )
    provider: str = Field(
        ...,
        description="The media provider for this artist.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="ARTIST",
        description="The type of content (always 'ARTIST' for artists)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'ARTIST' for artist objects."""
        if self.content_type != ContentType.ARTIST:
            raise ValueError("content_type must be 'ARTIST' for Artist objects")
        return self

class Playlist(GenericMediaBaseModel):
    """
    Internal storage model for playlists.
    
    Represents a playlist containing multiple tracks.
    """
    name: str = Field(
        ...,
        description="The name of the playlist.",
        min_length=1,
        max_length=500
    )
    track_ids: List[str] = Field(
        default_factory=list,
        description="List of track IDs included in this playlist."
    )
    is_personal: bool = Field(
        default=False,
        description="Whether this is a personal/private playlist or public."
    )
    provider: str = Field(
        ...,
        description="The media provider for this playlist.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="PLAYLIST",
        description="The type of content (always 'PLAYLIST' for playlists)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'PLAYLIST' for playlist objects."""
        if self.content_type != ContentType.PLAYLIST:
            raise ValueError("content_type must be 'PLAYLIST' for Playlist objects")
        return self

class PodcastEpisode(GenericMediaBaseModel):
    """
    Internal storage model for podcast episodes.
    
    Represents a single episode of a podcast show.
    """
    title: str = Field(
        ...,
        description="The title of the podcast episode.",
        min_length=1,
        max_length=500
    )
    show_id: str = Field(
        ...,
        description="The ID of the podcast show this episode belongs to.",
        min_length=1,
        max_length=100
    )
    provider: str = Field(
        ...,
        description="The media provider for this podcast episode.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="PODCAST_EPISODE",
        description="The type of content (always 'PODCAST_EPISODE' for episodes)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'PODCAST_EPISODE' for episode objects."""
        if self.content_type != ContentType.PODCAST_EPISODE:
            raise ValueError("content_type must be 'PODCAST_EPISODE' for PodcastEpisode objects")
        return self

class PodcastShow(GenericMediaBaseModel):
    """
    Internal storage model for podcast shows.
    
    Represents a podcast show containing multiple episodes.
    """
    title: str = Field(
        ...,
        description="The title of the podcast show.",
        min_length=1,
        max_length=500
    )
    episodes: List[PodcastEpisode] = Field(
        default_factory=list,
        description="List of podcast episodes in this show."
    )
    provider: str = Field(
        ...,
        description="The media provider for this podcast show.",
        min_length=1
    )
    content_type: ContentType = Field(
        default="PODCAST_SHOW",
        description="The type of content (always 'PODCAST_SHOW' for shows)."
    )

    @model_validator(mode='after')
    def validate_content_type(self):
        """Validate that content_type is 'PODCAST_SHOW' for show objects."""
        if self.content_type != ContentType.PODCAST_SHOW:
            raise ValueError("content_type must be 'PODCAST_SHOW' for PodcastShow objects")
        return self

    @model_validator(mode='after')
    def validate_episode_show_ids(self):
        """Validate that all episodes reference this show's ID."""
        for episode in self.episodes:
            if episode.show_id != self.id:
                raise ValueError(
                    f"Episode {episode.id} has show_id '{episode.show_id}' "
                    f"but should reference show ID '{self.id}'"
                )
        return self

class RecentlyPlayedItem(BaseModel):
    """
    Internal storage model for recently played items.
    
    Represents a media item that was recently played.
    """
    uri: str = Field(
        ...,
        description="The URI of the media item that was played.",
        min_length=1
    )
    timestamp: dt.datetime = Field(
        ...,
        description="The timestamp when the item was played in ISO 8601 format."
    )

class ActionLog(BaseModel):
    """
    Internal storage model for action logs.
    
    Represents an action performed on the media system for auditing purposes.
    """
    action_type: ActionType = Field(
        ...,
        description="The type of action performed (play or search)."
    )
    inputs: dict = Field(
        default_factory=dict,
        description="The inputs/parameters provided to the action (e.g., query, intent_type, filtering_type)."
    )
    outputs: List[dict] = Field(
        default_factory=list,
        description="The outputs/results returned by the action (list of media items)."
    )
    timestamp: dt.datetime = Field(
        ...,
        description="The timestamp when the action was performed in ISO 8601 format."
    )

class MediaItemMetadata(BaseModel):
    """
    Internal storage model for media item metadata.
    
    Contains metadata about a media item for display and identification.
    """
    entity_title: Optional[str] = Field(
        default=None,
        description="The title of the media entity.",
        max_length=500
    )
    container_title: Optional[str] = Field(
        default=None,
        description="The title of the container (album or show).",
        max_length=500
    )
    description: Optional[str] = Field(
        default=None,
        description="A description of the media item.",
        max_length=2000
    )
    artist_name: Optional[str] = Field(
        default=None,
        description="The name of the artist.",
        max_length=200
    )
    content_type: Optional[ContentType] = Field(
        default=None,
        description="The type of content."
    )

class MediaItem(BaseModel):
    """
    Internal storage model for media items.
    
    Represents a media item returned from search or play operations.
    """
    uri: str = Field(
        ...,
        description="The URI of the media item.",
        min_length=1
    )
    media_item_metadata: MediaItemMetadata = Field(
        ...,
        description="Metadata about the media item."
    )
    provider: Optional[str] = Field(
        default=None,
        description="The media provider for this item."
    )
    action_card_content_passthrough: Optional[str] = Field(
        default=None,
        description="Passthrough data for action cards."
    )

# ---------------------------
# Root Database Model
# ---------------------------

class GenericMediaDB(BaseModel):
    """
    Root model that validates the entire generic media database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for providers, tracks, albums, artists, playlists, podcasts, and recently played items.
    """
    providers: List[Provider] = Field(
        default_factory=list,
        description="List of media provider configurations."
    )
    actions: List[ActionLog] = Field(
        default_factory=list,
        description="Chronological log of executed actions (play/search) for auditing with full input/output tracking."
    )
    tracks: List[Track] = Field(
        default_factory=list,
        description="List of music tracks in the database."
    )
    albums: List[Album] = Field(
        default_factory=list,
        description="List of music albums in the database."
    )
    artists: List[Artist] = Field(
        default_factory=list,
        description="List of artists in the database."
    )
    playlists: List[Playlist] = Field(
        default_factory=list,
        description="List of playlists in the database."
    )
    podcasts: List[PodcastShow] = Field(
        default_factory=list,
        description="List of podcast shows in the database."
    )
    recently_played: List[RecentlyPlayedItem] = Field(
        default_factory=list,
        description="List of recently played media items."
    )

    class Config:
        str_strip_whitespace = True

    @model_validator(mode='after')
    def validate_referential_integrity(self):
        """Validate referential integrity across the database."""
        # Create sets for quick lookup
        track_ids = {track.id for track in self.tracks}
        
        # Validate album track references
        for album in self.albums:
            for track_id in album.track_ids:
                if track_id not in track_ids:
                    raise ValueError(
                        f"Album '{album.title}' (ID: {album.id}) references "
                        f"non-existent track ID: {track_id}"
                    )
        
        # Validate playlist track references
        for playlist in self.playlists:
            for track_id in playlist.track_ids:
                if track_id not in track_ids:
                    raise ValueError(
                        f"Playlist '{playlist.name}' (ID: {playlist.id}) references "
                        f"non-existent track ID: {track_id}"
                    )
        
        return self
