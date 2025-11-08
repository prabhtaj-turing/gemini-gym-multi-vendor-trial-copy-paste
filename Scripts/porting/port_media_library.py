"""
Media Library Database Porting Script

This module provides functionality to port media library data from vendor-specific
formats to the internal generic media database format. It handles tracks, albums,
podcasts, artists, and providers with proper data normalization and validation.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Setup path for imports
ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

# Import after path setup
from generic_media.SimulationEngine import db
from generic_media.SimulationEngine.models import (
    GenericMediaDB,
    Provider,
    Track,
    Album,
    Artist,
    Playlist,
    PodcastShow,
    PodcastEpisode,
)

# Constants
PROVIDER_URLS = {
    "Apple Music": "https://music.apple.com",
    "Spotify": "https://spotify.com",
    "Deezer": "https://www.deezer.com",
    "Amazon Music": "https://music.amazon.com",
    "SoundCloud": "https://soundcloud.com",
}

DEFAULT_OUTPUT_PATH = ROOT / "DBs" / "GenericMediaPortedDB.json"
TEMPLATE_DB_PATH = ROOT / "DBs" / "GenericMediaDefaultDB.json"


def string_to_iso_datetime(s: str) -> str:
    """
    Generate a deterministic ISO datetime string from input string.

    Creates a pseudo-random but deterministic timestamp based on the input string.
    Used for generating release timestamps when not provided in source data.

    Args:
        s: Input string to convert to datetime

    Returns:
        str: ISO format datetime string
    """
    # Generate deterministic number from string
    num = sum((i + 1) * ord(c) for i, c in enumerate(s))
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # Generate date within 30 years from base
    dt = base + timedelta(seconds=num % (60 * 60 * 24 * 365 * 30))
    return dt.isoformat()


def load_template_database() -> dict:
    """
    Load the template database from the default location.

    Returns:
        dict: Template database structure

    Raises:
        FileNotFoundError: If the template database file is not found
        json.JSONDecodeError: If the template file contains invalid JSON
    """
    with open(TEMPLATE_DB_PATH, "r") as f:
        return json.load(f)


def parse_source_database(source_json_str: str) -> dict:
    """
    Parse the source JSON string into a dictionary.

    Args:
        source_json_str: JSON string containing vendor media data

    Returns:
        dict: Parsed source database

    Raises:
        json.JSONDecodeError: If the source JSON string is invalid
    """
    return json.loads(source_json_str, strict=False)


def validate_provider_data(provider_data: dict) -> dict:
    """
    Validate provider data against Pydantic model.

    Args:
        provider_data: Raw provider data dictionary

    Returns:
        dict: Validated provider data

    Raises:
        ValueError: If validation fails
    """
    try:
        provider = Provider(**provider_data)
        return provider.model_dump()
    except Exception as e:
        raise ValueError(f"Provider validation failed: {e}") from e


def validate_track_data(track_data: dict) -> dict:
    """
    Validate track data against Pydantic model.

    Args:
        track_data: Raw track data dictionary

    Returns:
        dict: Validated track data

    Raises:
        ValueError: If validation fails
    """
    try:
        track = Track(**track_data)
        return track.model_dump()
    except Exception as e:
        raise ValueError(f"Track validation failed: {e}") from e


def validate_album_data(album_data: dict) -> dict:
    """
    Validate album data against Pydantic model.

    Args:
        album_data: Raw album data dictionary

    Returns:
        dict: Validated album data

    Raises:
        ValueError: If validation fails
    """
    try:
        album = Album(**album_data)
        return album.model_dump()
    except Exception as e:
        raise ValueError(f"Album validation failed: {e}") from e


def validate_artist_data(artist_data: dict) -> dict:
    """
    Validate artist data against Pydantic model.

    Args:
        artist_data: Raw artist data dictionary

    Returns:
        dict: Validated artist data

    Raises:
        ValueError: If validation fails
    """
    try:
        artist = Artist(**artist_data)
        return artist.model_dump()
    except Exception as e:
        raise ValueError(f"Artist validation failed: {e}") from e


def validate_playlist_data(playlist_data: dict) -> dict:
    """
    Validate playlist data against Pydantic model.

    Args:
        playlist_data: Raw playlist data dictionary

    Returns:
        dict: Validated playlist data

    Raises:
        ValueError: If validation fails
    """
    try:
        playlist = Playlist(**playlist_data)
        return playlist.model_dump()
    except Exception as e:
        raise ValueError(f"Playlist validation failed: {e}") from e


def validate_podcast_data(podcast_data: dict) -> dict:
    """
    Validate podcast data against Pydantic model.

    Args:
        podcast_data: Raw podcast data dictionary

    Returns:
        dict: Validated podcast data

    Raises:
        ValueError: If validation fails
    """
    try:
        # Validate episodes first
        validated_episodes = []
        for episode_data in podcast_data.get("episodes", []):
            episode = PodcastEpisode(**episode_data)
            validated_episodes.append(episode.model_dump())

        # Update podcast data with validated episodes
        podcast_data_copy = podcast_data.copy()
        podcast_data_copy["episodes"] = validated_episodes

        podcast = PodcastShow(**podcast_data_copy)

        return podcast.model_dump()
    except Exception as e:
        raise ValueError(f"Podcast validation failed: {e}") from e


def process_providers(source_providers: list, provider_template: dict) -> list:
    """
    Process provider data with URL mapping and normalization.

    Args:
        source_providers: List of source provider data
        provider_template: Template structure for providers

    Returns:
        list: Processed and validated providers with normalized URLs

    Raises:
        ValueError: If provider validation fails
    """
    processed_providers = []

    for src_provider in source_providers:
        new_provider = {}
        name = src_provider.get("name", "")

        for field in provider_template.keys():
            if field == "base_url":
                # Map known providers to their URLs, generate for unknown ones
                new_provider[field] = PROVIDER_URLS.get(
                    name, f"https://{name.replace(' ', '').lower()}.com"
                )
            else:
                new_provider[field] = src_provider.get(field, None)

        # Validate against Pydantic model
        validated_provider = validate_provider_data(new_provider)
        processed_providers.append(validated_provider)

    return processed_providers


def process_tracks(source_tracks: list, track_template: dict) -> list:
    """
    Process track data with ranking and timestamp generation.

    Args:
        source_tracks: List of source track data
        track_template: Template structure for tracks

    Returns:
        list: Processed and validated tracks with generated ranks and timestamps

    Raises:
        ValueError: If track validation fails
    """
    processed_tracks = []

    for idx, src_track in enumerate(source_tracks, start=1):
        new_track = {}
        for field in track_template.keys():
            if field in src_track:
                new_track[field] = src_track[field]
            else:
                # Generate default values for missing fields
                if field == "rank":
                    new_track[field] = idx
                elif field == "release_timestamp":
                    title = src_track.get("title", f"track_{idx}")
                    new_track[field] = string_to_iso_datetime(title)
                elif field == "is_liked":
                    new_track[field] = False
                else:
                    new_track[field] = None

        # Validate against Pydantic model
        validated_track = validate_track_data(new_track)
        processed_tracks.append(validated_track)

    return processed_tracks


def process_podcasts(source_podcasts: list, podcast_template: dict) -> list:
    """
    Process podcast data with episode structure preservation.

    Args:
        source_podcasts: List of source podcast data
        podcast_template: Template structure for podcasts

    Returns:
        list: Processed and validated podcasts with normalized episode data

    Raises:
        ValueError: If podcast validation fails
    """
    processed_podcasts = []

    for src_podcast in source_podcasts:
        new_podcast = {}
        for field in podcast_template.keys():
            if field == "episodes":
                new_podcast["episodes"] = []
                episode_template = (
                    podcast_template["episodes"][0]
                    if podcast_template.get("episodes")
                    else {}
                )
                # Process each episode
                for episode in src_podcast.get("episodes", []):
                    new_episode = {
                        field: episode.get(field, None)
                        for field in episode_template.keys()
                    }
                    new_podcast["episodes"].append(new_episode)
            else:
                new_podcast[field] = src_podcast.get(field, None)

        # Validate against Pydantic model
        validated_podcast = validate_podcast_data(new_podcast)
        processed_podcasts.append(validated_podcast)

    return processed_podcasts


def process_generic_list(
    source_items: list, template_item: dict, data_type: str = "generic"
) -> list:
    """
    Process generic list-based data structures with optional validation.

    Args:
        source_items: List of source items
        template_item: Template structure for items
        data_type: Type of data for validation ('albums', 'playlists', or 'generic')

    Returns:
        list: Processed items following template structure

    Raises:
        ValueError: If validation fails for known data types
    """
    processed_items = []

    for src_item in source_items:
        new_item = {field: src_item.get(field, None) for field in template_item.keys()}

        # Apply validation for known data types
        if data_type == "albums":
            validated_item = validate_album_data(new_item)
        elif data_type == "playlists":
            validated_item = validate_playlist_data(new_item)
        else:
            # For unknown types, just return the processed item without validation
            validated_item = new_item

        processed_items.append(validated_item)

    return processed_items


def create_empty_structure(template_val):
    """
    Create empty structure based on template type.

    Args:
        template_val: Template value to determine structure type

    Returns:
        Empty structure (list, dict, or None)
    """
    if isinstance(template_val, list):
        return []
    elif isinstance(template_val, dict):
        return {}
    else:
        return None


def generate_artists(ported_db: dict) -> None:
    """
    Generate artist entries from tracks and albums data.

    Creates a unique list of artists based on artist_name and provider
    from both tracks and albums. Ensures no duplicate artists are created.

    Args:
        ported_db: The ported database to add artists to

    Raises:
        ValueError: If artist validation fails
    """
    artist_dict = {}  # (artist_name, provider) -> id
    artists = []
    counter = 1

    # Extract artists from tracks
    for track in ported_db.get("tracks", []):
        name = track.get("artist_name")
        provider = track.get("provider", "unknown")
        if name and (name, provider) not in artist_dict:
            artist_id = f"artist_{counter}"
            counter += 1
            artist_dict[(name, provider)] = artist_id

            artist_data = {
                "id": artist_id,
                "name": name,
                "provider": provider,
                "content_type": "ARTIST",
            }
            # Validate against Pydantic model
            validated_artist = validate_artist_data(artist_data)
            artists.append(validated_artist)

    # Extract artists from albums
    for album in ported_db.get("albums", []):
        name = album.get("artist_name")
        provider = album.get("provider", "unknown")
        if name and (name, provider) not in artist_dict:
            artist_id = f"artist_{counter}"
            counter += 1
            artist_dict[(name, provider)] = artist_id

            artist_data = {
                "id": artist_id,
                "name": name,
                "provider": provider,
                "content_type": "ARTIST",
            }
            # Validate against Pydantic model
            validated_artist = validate_artist_data(artist_data)
            artists.append(validated_artist)

    ported_db["artists"] = artists


def save_ported_database(ported_db: dict, output_path: str | None = None) -> Path:
    """
    Save the ported database to file and load it into the simulation engine.

    Args:
        ported_db: The ported database to save
        output_path: Optional path to save the database. If None, uses default location.

    Returns:
        Path: Path where the database was saved
    """
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = DEFAULT_OUTPUT_PATH

    output_file.write_text(json.dumps(ported_db, indent=2), encoding="utf-8")
    db.load_state(str(output_file))

    return output_file


def validate_complete_database(ported_db: dict) -> dict:
    """
    Validate the complete database structure against the GenericMediaDB model.

    Args:
        ported_db: The complete ported database

    Returns:
        dict: Validated database structure

    Raises:
        ValueError: If database validation fails
    """
    try:
        # Validate the complete database structure
        db_model = GenericMediaDB(**ported_db)
        return db_model.model_dump()
    except Exception as e:
        raise ValueError(f"Database validation failed: {e}") from e


def process_database_section(key: str, template_val, source_db: dict):
    """
    Process a specific section of the database based on its type and key.

    Args:
        key: The database section key (e.g., 'providers', 'tracks', etc.)
        template_val: Template structure for this section
        source_db: Source database containing the data

    Returns:
        Processed data for this section
    """
    if key not in source_db:
        return create_empty_structure(template_val)

    if key == "providers":
        provider_template = template_val[0] if template_val else {}
        return process_providers(source_db[key], provider_template)

    elif (
        isinstance(template_val, list)
        and template_val
        and isinstance(template_val[0], dict)
    ):
        template_item = template_val[0]

        if key == "tracks":
            return process_tracks(source_db[key], template_item)
        elif key == "podcasts":
            return process_podcasts(source_db[key], template_item)
        else:
            return process_generic_list(source_db[key], template_item, key)

    else:
        # Copy other data directly
        return source_db[key]


def port_media_library(source_json_str: str, output_path: str | None = None) -> dict:
    """
    Port media library database from vendor format to internal generic media format.

    This function takes a JSON string containing vendor-specific media data and
    converts it to the standardized internal format. It handles:
    - Provider URL mapping and normalization
    - Track ranking and timestamp generation
    - Podcast episode structure preservation
    - Artist generation from tracks and albums
    - Data validation and type conversion

    Args:
        source_json_str: JSON string containing vendor media data
        output_path: Optional path to save the ported database. If None, saves to default location.

    Returns:
        dict: The ported media database in internal format

    Raises:
        FileNotFoundError: If the template database file is not found
        json.JSONDecodeError: If the source JSON string is invalid
        ValueError: If data validation fails
    """
    # Load template and source databases
    template_db = load_template_database()
    source_db = parse_source_database(source_json_str)

    # Process each section of the database
    ported_db = {}
    for key, template_val in template_db.items():
        ported_db[key] = process_database_section(key, template_val, source_db)

    # Generate artists from tracks and albums
    generate_artists(ported_db)

    # Validate the complete database structure
    validated_db = validate_complete_database(ported_db)

    # Save the ported database
    save_ported_database(validated_db, output_path)

    return validated_db


def get_input_data() -> tuple[str, str | None]:
    """
    Get input data and output path from command line or default files.

    Returns:
        tuple: (raw_input_data, output_path)

    Raises:
        FileNotFoundError: If default input file doesn't exist
        OSError: If there's an issue reading from stdin or file
    """
    try:
        if not sys.stdin.isatty():
            # Read from stdin if available
            raw_input = sys.stdin.read().strip()
            output_path = sys.argv[1] if len(sys.argv) > 1 else None
        else:
            # Use default file paths
            base_path = Path(__file__).resolve().parent / "SampleDBs" / "media_library"
            input_file = base_path / "vendor_media_library.json"
            output_path = str(base_path / "final_vendor_media_library.json")

            if not input_file.exists():
                raise FileNotFoundError(f"Default input file not found: {input_file}")

            raw_input = input_file.read_text(encoding="utf-8")

        return raw_input, output_path

    except OSError as e:
        raise OSError(f"Error reading input data: {e}") from e


if __name__ == "__main__":
    """
    Main execution function with proper error handling.
    """
    try:
        raw_input, output_path = get_input_data()
        ported_db = port_media_library(raw_input, output_path)
        print("Ported Generic Media DB loaded successfully.")
        print(
            f"Database contains {len(ported_db.get('tracks', []))} tracks, "
            f"{len(ported_db.get('albums', []))} albums, "
            f"{len(ported_db.get('artists', []))} artists, "
            f"{len(ported_db.get('providers', []))} providers"
        )

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in input data: {e}", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:
        print(f"Error: Data validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
