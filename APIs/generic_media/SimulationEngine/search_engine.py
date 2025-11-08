from typing import List, Dict, Union
from common_utils.search_engine.models import SearchableDocument
from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.engine import search_engine_manager
from .models import Track, Album, Artist, Playlist, PodcastShow, PodcastEpisode
from .db import DB


class ServiceAdapter(Adapter):
    """Adapter creates distinct, searchable chunks for each media type."""

    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """
        Convert the database to searchable documents.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        items = self._get_all_data()
        searchable_documents = []
        for item in items:
            if isinstance(item, Track):
                searchable_documents.extend(self._adapt_track(item))
            elif isinstance(item, Album):
                searchable_documents.extend(self._adapt_album(item))
            elif isinstance(item, Artist):
                searchable_documents.extend(self._adapt_artist(item))
            elif isinstance(item, Playlist):
                searchable_documents.extend(self._adapt_playlist(item))
            elif isinstance(item, PodcastShow):
                searchable_documents.extend(self._adapt_podcast_show(item))
            elif isinstance(item, PodcastEpisode):
                searchable_documents.extend(self._adapt_podcast_episode(item))
        return searchable_documents

    def _get_all_data(self) -> List[Union[Track, Album, Artist, Playlist, PodcastShow, PodcastEpisode]]:
        """
        Get all data from the database.

        Returns:
            List[Union[Track, Album, Artist, Playlist, PodcastShow, PodcastEpisode]]: List of all data.
        """
        tracks = [Track(**track) for track in DB.get("tracks", [])]
        albums = [Album(**album) for album in DB.get("albums", [])]
        artists = [Artist(**artist) for artist in DB.get("artists", [])]
        playlists = [Playlist(**playlist) for playlist in DB.get("playlists", [])]
        podcasts = [PodcastShow(**podcast) for podcast in DB.get("podcasts", [])]
        episodes = [episode for podcast in podcasts for episode in podcast.episodes]
        items = tracks + albums + artists + playlists + podcasts + episodes
        return items

    def _make_chunk(
        self,
        parent_id: str,
        text_content: str,
        original_json_obj: Union[Track, Album, Artist, Playlist, PodcastShow, PodcastEpisode],
        metadata: Dict[str, Union[str, bool]],
    ) -> SearchableDocument:
        """
        Make a chunk from the given data.

        Args:
            parent_id (str): The parent ID.
            text_content (str): The text content.
            original_json_obj (Union[Track, Album, Artist, Playlist, PodcastShow, PodcastEpisode]): The original JSON object.
            metadata (Dict[str, Union[str, bool]]): The metadata.

        Returns:
            SearchableDocument: The searchable document.
        """
        base_metadata = {"resource_type": "media"}
        base_metadata.update(metadata)
        return SearchableDocument(
            parent_doc_id=parent_id,
            text_content=text_content,
            original_json_obj=original_json_obj,
            metadata=base_metadata,
        )

    def _adapt_track(self, track: Track) -> List[SearchableDocument]:
        """
        Adapt the track to a searchable document.

        Args:
            track (Track): The track to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"track_{track.id}"
        text_content = f"TRACK: {track.title} {track.artist_name}"
        metadata = {
            "content_type": "TRACK",
            "is_liked": str(track.is_liked),
            "is_personal": "False",
        }
        return [
            self._make_chunk(
                parent_id, text_content, track.model_dump(mode="json"), metadata
            )
        ]

    def _adapt_album(self, album: Album) -> List[SearchableDocument]:
        """
        Adapt the album to a searchable document.

        Args:
            album (Album): The album to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"album_{album.id}"
        text_content = f"ALBUM: {album.title} {album.artist_name}"
        metadata = {"content_type": "ALBUM"}
        return [
            self._make_chunk(
                parent_id, text_content, album.model_dump(mode="json"), metadata
            )
        ]

    def _adapt_artist(self, artist: Artist) -> List[SearchableDocument]:
        """
        Adapt the artist to a searchable document.

        Args:
            artist (Artist): The artist to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"artist_{artist.id}"
        text_content = f"ARTIST: {artist.name}"
        metadata = {"content_type": "ARTIST"}
        return [
            self._make_chunk(
                parent_id, text_content, artist.model_dump(mode="json"), metadata
            )
        ]

    def _adapt_playlist(self, playlist: Playlist) -> List[SearchableDocument]:
        """
        Adapt the playlist to a searchable document.

        Args:
            playlist (Playlist): The playlist to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"playlist_{playlist.id}"
        playlist_type = (
            "PERSONAL_PLAYLIST" if playlist.is_personal else "PUBLIC_PLAYLIST"
        )
        text_content = f"{playlist_type}: {playlist.name}"
        metadata = {
            "content_type": "PLAYLIST",
            "is_personal": str(playlist.is_personal),
            "is_liked": "False",
        }
        return [
            self._make_chunk(
                parent_id, text_content, playlist.model_dump(mode="json"), metadata
            )
        ]

    def _adapt_podcast_show(
        self, podcast_show: PodcastShow
    ) -> List[SearchableDocument]:
        """
        Adapt the podcast show to a searchable document.

        Args:
            podcast_show (PodcastShow): The podcast show to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"podcast_show_{podcast_show.id}"
        text_content = f"PODCAST_SHOW: {podcast_show.title}"
        metadata = {"content_type": "PODCAST_SHOW"}
        return [
            self._make_chunk(
                parent_id, text_content, podcast_show.model_dump(mode="json"), metadata
            )
        ]

    def _adapt_podcast_episode(
        self, podcast_episode: PodcastEpisode
    ) -> List[SearchableDocument]:
        """
        Adapt the podcast episode to a searchable document.

        Args:
            podcast_episode (PodcastEpisode): The podcast episode to adapt.

        Returns:
            List[SearchableDocument]: List of searchable documents.
        """
        parent_id = f"podcast_episode_{podcast_episode.id}"
        text_content = f"PODCAST_EPISODE: {podcast_episode.title}"
        metadata = {"content_type": "PODCAST_EPISODE"}
        return [
            self._make_chunk(
                parent_id,
                text_content,
                podcast_episode.model_dump(mode="json"),
                metadata,
            )
        ]


service_adapter = ServiceAdapter()
search_engine_manager = search_engine_manager.get_engine_manager("generic_media")

__all__ = ["service_adapter", "search_engine_manager"]
