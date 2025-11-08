from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base models for Spotify API entities that match the default database structure

class SpotifyImage(BaseModel):
    """Model for Spotify image objects."""
    height: Optional[int] = None
    url: str
    width: Optional[int] = None

class SpotifyExternalUrls(BaseModel):
    """Model for Spotify external URLs."""
    spotify: str

class SpotifyFollowers(BaseModel):
    """Model for Spotify followers information."""
    href: Optional[str] = None
    total: int

class SpotifyCopyright(BaseModel):
    """Model for Spotify copyright information."""
    text: str
    type: str

class SpotifyExternalIds(BaseModel):
    """Model for Spotify external IDs."""
    isrc: Optional[str] = None

class SpotifyResumePoint(BaseModel):
    """Model for resume point information in episodes."""
    fully_played: bool
    resume_position_ms: int

class SpotifyRecommendationSeeds(BaseModel):
    """Model for recommendation seeds."""
    genres: List[str]
    artists: List[str]
    tracks: List[str]

class SpotifyArtistSimple(BaseModel):
    """Simplified model for artist references."""
    id: str
    name: str

class SpotifyAlbumSimple(BaseModel):
    """Simplified model for album references."""
    id: str
    name: str
    album_type: Optional[str] = None
    total_tracks: Optional[int] = None
    available_markets: Optional[List[str]] = None
    external_urls: Optional[SpotifyExternalUrls] = None
    href: Optional[str] = None
    images: Optional[List[SpotifyImage]] = None
    release_date: Optional[str] = None
    release_date_precision: Optional[str] = None
    restrictions: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    uri: Optional[str] = None

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate release date format using centralized validation."""
        if v is None:
            return v
        from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
        try:
            return validate_date_only(v)
        except InvalidDateTimeFormatError as e:
            from spotify.SimulationEngine.custom_errors import InvalidDateTimeFormatError as SpotifyInvalidDateTimeFormatError
            raise SpotifyInvalidDateTimeFormatError(f"Invalid album simple release date format: {e}")

class SpotifyShowSimple(BaseModel):
    """Simplified model for show references."""
    id: str
    name: str

class SpotifyUserSimple(BaseModel):
    """Simplified model for user references."""
    id: str
    display_name: str
    external_urls: Optional[SpotifyExternalUrls] = None
    href: Optional[str] = None
    type: Optional[str] = None
    uri: Optional[str] = None

class SpotifyArtist(BaseModel):
    """Model for Spotify artist objects as stored in default DB."""
    id: str
    name: str
    type: str = "artist"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    genres: Optional[List[str]] = None
    popularity: Optional[int] = None
    images: Optional[List[SpotifyImage]] = None
    followers: Optional[SpotifyFollowers] = None

class SpotifyAlbum(BaseModel):
    """Model for Spotify album objects as stored in default DB."""
    id: str
    name: str
    type: str = "album"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    artists: List[SpotifyArtistSimple]
    album_type: str
    total_tracks: int
    available_markets: Optional[List[str]] = None
    release_date: str
    release_date_precision: str
    images: Optional[List[SpotifyImage]] = None
    popularity: Optional[int] = None

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, v: str) -> str:
        """Validate release date format using centralized validation."""
        from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
        try:
            return validate_date_only(v)
        except InvalidDateTimeFormatError as e:
            from spotify.SimulationEngine.custom_errors import InvalidDateTimeFormatError as SpotifyInvalidDateTimeFormatError
            raise SpotifyInvalidDateTimeFormatError(f"Invalid album release date format: {e}")
    copyrights: List[SpotifyCopyright]
    external_ids: SpotifyExternalIds
    label: str
    restrictions: Optional[Dict[str, Any]] = None
    genres: Optional[List[str]] = None

class SpotifyTrack(BaseModel):
    """Model for Spotify track objects as stored in default DB."""
    id: str
    name: str
    type: str = "track"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    artists: List[SpotifyArtistSimple]
    album: SpotifyAlbumSimple
    duration_ms: int
    explicit: bool
    track_number: int
    disc_number: int
    available_markets: Optional[List[str]] = None
    popularity: Optional[int] = None
    is_local: bool
    is_playable: bool
    external_ids: Optional[SpotifyExternalIds] = None
    linked_from: Optional[Any] = None
    restrictions: Optional[Dict[str, Any]] = None
    preview_url: Optional[str] = None

class SpotifyExplicitContentSettings(BaseModel):
    """Model for explicit content settings."""
    filter_enabled: bool
    filter_locked: bool

class SpotifyUser(BaseModel):
    """Model for Spotify user objects as stored in default DB."""
    id: str
    display_name: str
    type: str = "user"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    followers: Optional[SpotifyFollowers] = None
    images: Optional[List[SpotifyImage]] = None
    country: Optional[str] = None
    email: Optional[str] = None
    product: Optional[str] = None
    explicit_content: Optional[SpotifyExplicitContentSettings] = None

class SpotifyTracksInfo(BaseModel):
    """Model for tracks information in playlists."""
    total: int

class SpotifyPlaylist(BaseModel):
    """Model for Spotify playlist objects as stored in default DB."""
    id: str
    name: str
    type: str = "playlist"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    owner: SpotifyUserSimple
    public: bool
    collaborative: bool
    description: Optional[str] = None
    images: Optional[List[SpotifyImage]] = None
    tracks: SpotifyTracksInfo
    followers: Optional[SpotifyFollowers] = None
    snapshot_id: Optional[str] = None

class SpotifyPlaylistTrack(BaseModel):
    """Model for tracks within playlists as stored in default DB."""
    added_at: str
    added_by: SpotifyUserSimple
    is_local: bool
    track: SpotifyTrack

class SpotifyCategory(BaseModel):
    """Model for Spotify category objects as stored in default DB."""
    id: str
    name: str
    type: str = "category"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    icons: Optional[List[SpotifyImage]] = None

class SpotifyShow(BaseModel):
    """Model for Spotify show objects as stored in default DB."""
    id: str
    name: str
    type: str = "show"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    publisher: str
    description: str
    html_description: Optional[str] = None
    explicit: bool
    available_markets: Optional[List[str]] = None
    copyrights: Optional[List[SpotifyCopyright]] = None
    is_externally_hosted: bool
    languages: List[str]
    media_type: str
    total_episodes: int
    episodes: Optional[List[str]] = None
    images: Optional[List[SpotifyImage]] = None

class SpotifyEpisode(BaseModel):
    """Model for Spotify episode objects as stored in default DB."""
    id: str
    name: str
    type: str = "episode"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    show: SpotifyShowSimple
    description: str
    html_description: Optional[str] = None
    duration_ms: int
    release_date: str
    release_date_precision: str
    explicit: bool
    images: Optional[List[SpotifyImage]] = None
    is_externally_hosted: bool
    is_playable: bool
    language: str
    languages: List[str]
    audio_preview_url: Optional[str] = None
    resume_point: SpotifyResumePoint
    restrictions: Optional[Dict[str, Any]] = None

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, v: str) -> str:
        """Validate release date format using centralized validation."""
        from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
        try:
            return validate_date_only(v)
        except InvalidDateTimeFormatError as e:
            from spotify.SimulationEngine.custom_errors import InvalidDateTimeFormatError as SpotifyInvalidDateTimeFormatError
            raise SpotifyInvalidDateTimeFormatError(f"Invalid episode release date format: {e}")

class SpotifyAuthor(BaseModel):
    """Model for audiobook authors."""
    name: str

class SpotifyNarrator(BaseModel):
    """Model for audiobook narrators."""
    name: str

class SpotifyAudiobookSimple(BaseModel):
    """Simplified model for audiobook references."""
    id: str
    name: str
    type: Optional[str] = None
    uri: Optional[str] = None
    href: Optional[str] = None
    external_urls: Optional[SpotifyExternalUrls] = None
    authors: Optional[List[SpotifyAuthor]] = None
    available_markets: Optional[List[str]] = None
    copyrights: Optional[List[SpotifyCopyright]] = None
    description: Optional[str] = None
    html_description: Optional[str] = None
    edition: Optional[str] = None
    explicit: Optional[bool] = None
    images: Optional[List[SpotifyImage]] = None
    languages: Optional[List[str]] = None
    media_type: Optional[str] = None
    narrators: Optional[List[SpotifyNarrator]] = None
    publisher: Optional[str] = None
    total_chapters: Optional[int] = None

class SpotifyAudiobook(BaseModel):
    """Model for Spotify audiobook objects as stored in default DB."""
    id: str
    name: str
    type: str = "audiobook"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    authors: Optional[List[str]] = None
    narrators: Optional[List[str]] = None
    chapters: Optional[List[str]] = None
    description: str
    duration_ms: int
    language: str
    explicit: bool
    images: Optional[List[SpotifyImage]] = None
    total_chapters: int
    available_markets: Optional[List[str]] = None
    copyrights: Optional[List[SpotifyCopyright]] = None
    html_description: Optional[str] = None
    edition: Optional[str] = None
    media_type: Optional[str] = None
    publisher: Optional[str] = None

class SpotifyChapter(BaseModel):
    """Model for Spotify chapter objects as stored in default DB."""
    id: str
    name: str
    type: str = "chapter"
    uri: str
    href: str
    external_urls: SpotifyExternalUrls
    duration_ms: int
    description: str
    html_description: Optional[str] = None
    audio_preview_url: Optional[str] = None
    images: Optional[List[SpotifyImage]] = None
    languages: List[str]
    available_markets: Optional[List[str]] = None
    chapter_number: int
    explicit: bool
    is_playable: bool
    release_date: str
    release_date_precision: str
    resume_point: SpotifyResumePoint
    restrictions: Optional[Dict[str, Any]] = None
    audiobook: Optional[SpotifyAudiobookSimple] = None

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, v: str) -> str:
        """Validate release date format using centralized validation."""
        from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
        try:
            return validate_date_only(v)
        except InvalidDateTimeFormatError as e:
            from spotify.SimulationEngine.custom_errors import InvalidDateTimeFormatError as SpotifyInvalidDateTimeFormatError
            raise SpotifyInvalidDateTimeFormatError(f"Invalid chapter release date format: {e}")

class SpotifyDevice(BaseModel):
    """Model for Spotify device objects as stored in default DB."""
    id: str
    name: str
    type: str
    is_active: bool
    is_private_session: Optional[bool] = None
    is_restricted: Optional[bool] = None
    volume_percent: Optional[int] = None
    supports_volume: Optional[bool] = None
    capabilities: Optional[Dict[str, bool]] = None

class SpotifyAudioFeatures(BaseModel):
    """Model for Spotify audio features as stored in default DB."""
    id: str
    acousticness: float
    analysis_url: str
    danceability: float
    duration_ms: int
    energy: float
    instrumentalness: float
    key: int
    liveness: float
    loudness: float
    mode: int
    speechiness: float
    tempo: float
    time_signature: int
    track_href: str
    type: str = "audio_features"
    uri: str
    valence: float

class SpotifyAudioAnalysisMeta(BaseModel):
    """Model for audio analysis metadata."""
    analyzer_version: str
    platform: str
    detailed_status: str
    status_code: int
    timestamp: int
    analysis_time: float
    input_process: str

class SpotifyAudioAnalysisTrack(BaseModel):
    """Model for audio analysis track data."""
    num_samples: int
    duration: float
    sample_md5: str
    offset_seconds: int
    window_seconds: int
    analysis_sample_rate: int
    analysis_channels: int
    end_of_fade_in: float
    start_of_fade_out: float
    loudness: float
    tempo: float
    tempo_confidence: float
    time_signature: int
    time_signature_confidence: float
    key: int
    key_confidence: float
    mode: int
    mode_confidence: float

class SpotifyAudioAnalysisSegment(BaseModel):
    """Model for audio analysis segments."""
    start: float
    duration: float
    confidence: float
    loudness_start: float
    loudness_max_time: float
    loudness_max: float
    loudness_end: float
    pitches: List[float]
    timbre: List[float]

class SpotifyAudioAnalysisSection(BaseModel):
    """Model for audio analysis sections."""
    start: float
    duration: float
    confidence: float
    loudness: float
    tempo: float
    tempo_confidence: float
    key: int
    key_confidence: float
    mode: int
    mode_confidence: float
    time_signature: int
    time_signature_confidence: float

class SpotifyAudioAnalysis(BaseModel):
    """Model for Spotify audio analysis as stored in default DB."""
    meta: SpotifyAudioAnalysisMeta
    track: SpotifyAudioAnalysisTrack
    segments: List[SpotifyAudioAnalysisSegment]
    sections: List[SpotifyAudioAnalysisSection]

class SpotifyRecentlyPlayedItem(BaseModel):
    """Model for recently played items."""
    track: str
    played_at: str

class SpotifyQueue(BaseModel):
    """Model for user playback queue."""
    currently_playing: Optional[SpotifyTrack] = None
    queue: List[SpotifyTrack]

class SpotifyUserSettings(BaseModel):
    """Model for user settings."""
    explicit_content: bool
    theme: str

class SpotifyUserExplicitContentSettings(BaseModel):
    """Model for user explicit content settings."""
    filter_enabled: bool

class SpotifyActions(BaseModel):
    """Model for playback actions."""
    disallows: Dict[str, bool]

class SpotifyPlaybackState(BaseModel):
    """Model for playback state."""
    device: SpotifyDevice
    shuffle_state: bool
    repeat_state: str
    is_playing: bool
    progress_ms: int
    item: SpotifyTrack
    currently_playing_type: str
    actions: SpotifyActions

class SpotifyContext(BaseModel):
    """Model for playback context."""
    type: str
    href: str
    external_urls: SpotifyExternalUrls
    uri: str

class SpotifyCurrentlyPlaying(BaseModel):
    """Model for currently playing item."""
    timestamp: int
    context: SpotifyContext
    progress_ms: int
    item: SpotifyTrack
    currently_playing_type: str
    actions: SpotifyActions
    is_playing: bool
    device: SpotifyDevice
    repeat_state: str
    shuffle_state: bool

class SpotifyEnhancedEpisode(BaseModel):
    """Model for enhanced episode objects."""
    id: str
    name: str
    show: SpotifyShowSimple
    description: str
    duration_ms: int
    release_date: str
    language: str
    resume_point: SpotifyResumePoint
    explicit: bool
    images: Optional[List[SpotifyImage]] = None
    external_urls: SpotifyExternalUrls
    href: str
    uri: str

    @field_validator("release_date")
    @classmethod
    def validate_release_date(cls, v: str) -> str:
        """Validate release date format using centralized validation."""
        from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
        try:
            return validate_date_only(v)
        except InvalidDateTimeFormatError as e:
            from spotify.SimulationEngine.custom_errors import InvalidDateTimeFormatError as SpotifyInvalidDateTimeFormatError
            raise SpotifyInvalidDateTimeFormatError(f"Invalid enhanced episode release date format: {e}")

class SpotifyEnhancedAudiobook(BaseModel):
    """Model for enhanced audiobook objects."""
    id: str
    name: str
    authors: Optional[List[str]] = None
    narrators: Optional[List[str]] = None
    chapters: Optional[List[str]] = None
    description: str
    duration_ms: int
    language: str
    explicit: bool
    images: Optional[List[SpotifyImage]] = None
    external_urls: SpotifyExternalUrls
    href: str
    uri: str
    total_chapters: int

class SpotifyEnhancedChapter(BaseModel):
    """Model for enhanced chapter objects."""
    id: str
    name: str
    duration_ms: int
    description: str
    audio_preview_url: str
    images: Optional[List[SpotifyImage]] = None
    external_urls: SpotifyExternalUrls
    href: str
    uri: str
    languages: List[str]

class SpotifyEnhancedPlaylistTrack(BaseModel):
    """Model for enhanced playlist track objects."""
    added_at: str
    added_by: SpotifyUserSimple
    is_local: bool
    track: SpotifyTrack

class SpotifyEnhancedDevice(BaseModel):
    """Model for enhanced device objects."""
    id: str
    name: str
    type: str
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    volume_percent: int
    capabilities: Dict[str, bool]

class SpotifyTopArtists(BaseModel):
    """Model for user's top artists."""
    artists: List[SpotifyArtist]

class SpotifyTopTracks(BaseModel):
    """Model for user's top tracks."""
    tracks: List[SpotifyTrack]

# Simplified models for collections that have reduced data
class SpotifyArtistSimplified(BaseModel):
    """Simplified artist model for top_artists collection."""
    id: str
    name: str
    genres: Optional[List[str]] = None
    popularity: Optional[int] = None
    images: Optional[List[SpotifyImage]] = None
    followers: Optional[SpotifyFollowers] = None

class SpotifyTrackSimplified(BaseModel):
    """Simplified track model for top_tracks and enhanced_playlist_tracks collections."""
    id: str
    name: str
    artists: List[SpotifyArtistSimple]
    album: SpotifyAlbumSimple
    duration_ms: int
    explicit: bool
    track_number: int
    disc_number: int
    available_markets: Optional[List[str]] = None
    popularity: Optional[int] = None

class SpotifyTopArtistsSimplified(BaseModel):
    """Model for user's top artists with simplified structure."""
    artists: List[SpotifyArtistSimplified]

class SpotifyTopTracksSimplified(BaseModel):
    """Model for user's top tracks with simplified structure."""
    tracks: List[SpotifyTrackSimplified]

class SpotifyEnhancedPlaylistTrackSimplified(BaseModel):
    """Model for enhanced playlist track objects with simplified track structure."""
    added_at: str
    added_by: SpotifyUserSimple
    is_local: bool
    track: SpotifyTrackSimplified

# Main database model that validates the entire SpotifyDefaultDB.json structure
class SpotifyDB(BaseModel):
    """
    Complete model for validating the entire Spotify default database structure.
    This model matches the structure of SpotifyDefaultDB.json exactly.
    """
    
    # Core entity collections
    albums: Dict[str, SpotifyAlbum]
    artists: Dict[str, SpotifyArtist]
    tracks: Dict[str, SpotifyTrack]
    playlists: Dict[str, SpotifyPlaylist]
    users: Dict[str, SpotifyUser]
    categories: Dict[str, SpotifyCategory]
    shows: Dict[str, SpotifyShow]
    episodes: Dict[str, SpotifyEpisode]
    audiobooks: Dict[str, SpotifyAudiobook]
    chapters: Dict[str, SpotifyChapter]
    
    # Relationship collections
    playlist_tracks: Dict[str, List[SpotifyPlaylistTrack]]
    user_playlists: Dict[str, List[str]]
    saved_albums: Dict[str, List[str]]
    followed_artists: Dict[str, List[str]]
    followed_playlists: Dict[str, List[str]]
    followed_users: Dict[str, List[str]]
    saved_tracks: Dict[str, List[str]]
    saved_shows: Dict[str, List[str]]
    saved_episodes: Dict[str, List[str]]
    saved_audiobooks: Dict[str, List[str]]
    
    # User activity and preferences
    user_recently_played: Dict[str, List[SpotifyRecentlyPlayedItem]]
    user_queue: Dict[str, SpotifyQueue]
    user_devices: Dict[str, List[SpotifyDevice]]
    playback_state: Dict[str, SpotifyPlaybackState]
    currently_playing: Dict[str, SpotifyCurrentlyPlaying]
    user_settings: Dict[str, SpotifyUserSettings]
    user_subscriptions: Dict[str, List[str]]
    user_explicit_content_settings: Dict[str, SpotifyUserExplicitContentSettings]
    user_following: Dict[str, List[str]]
    artist_following: Dict[str, List[str]]
    
    # Top content (using simplified models for reduced data)
    top_artists: Dict[str, SpotifyTopArtistsSimplified]
    top_tracks: Dict[str, SpotifyTopTracksSimplified]
    
    # Audio analysis and features
    audio_features: Dict[str, SpotifyAudioFeatures]
    audio_analysis: Dict[str, SpotifyAudioAnalysis]
    
    # Browse and discovery
    genres: List[str]
    featured_playlists: List[str]
    recommendations: Dict[str, List[str]]
    category_playlists: Dict[str, List[str]]
    related_artists: Dict[str, List[str]]
    recommendation_seeds: SpotifyRecommendationSeeds
    
    # Enhanced collections (using simplified models for reduced data)
    enhanced_episodes: Dict[str, SpotifyEnhancedEpisode]
    enhanced_audiobooks: Dict[str, SpotifyEnhancedAudiobook]
    enhanced_chapters: Dict[str, SpotifyEnhancedChapter]
    enhanced_playlist_tracks: Dict[str, List[SpotifyEnhancedPlaylistTrackSimplified]]
    enhanced_devices: Dict[str, List[SpotifyEnhancedDevice]]
    
    # Playlist and image management
    playlist_images: Dict[str, List[SpotifyImage]]
    playlist_cover_images: Dict[str, List[SpotifyImage]]
    playlist_followers: Dict[str, List[str]]
    
    # Market and regional data
    markets: List[str]
    
    # Current user
    current_user: Dict[str, str]
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Don't allow extra fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values in serialization

