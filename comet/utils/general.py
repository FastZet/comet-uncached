import base64
import hashlib
import json
import re
import aiohttp
import bencodepy

from RTN import parse, title_match
from curl_cffi import requests
from databases import Database

from comet.utils.logger import logger
from comet.utils.models import settings, ConfigModel

languages_emojis = {
    "multi_subs": "🌐",
    "multi_audio": "🌎",
    "dual_audio": "🔉",
    "english": "🇬🇧",
    "japanese": "🇯🇵",
    "korean": "🇰🇷",
    "taiwanese": "🇹🇼",
    "chinese": "🇨🇳",
    "french": "🇫🇷",
    "latino": "💃🏻",
    "spanish": "🇪🇸",
    "portuguese": "🇵🇹",
    "italian": "🇮🇹",
    "greek": "🇬🇷",
    "german": "🇩🇪",
    "russian": "🇷🇺",
    "ukrainian": "🇺🇦",
    "hindi": "🇮🇳",
    "telugu": "🇮🇳",
    "tamil": "🇮🇳",
    "lithuanian": "🇱🇹",
    "latvian": "🇱🇻",
    "estonian": "🇪🇪",
    "polish": "🇵🇱",
    "czech": "🇨🇿",
    "slovakian": "🇸🇰",
    "hungarian": "🇭🇺",
    "romanian": "🇷🇴",
    "bulgarian": "🇧🇬",
    "serbian": "🇷🇸",
    "croatian": "🇭🇷",
    "slovenian": "🇸🇮",
    "dutch": "🇳🇱",
    "danish": "🇩🇰",
    "finnish": "🇫🇮",
    "swedish": "🇸🇪",
    "norwegian": "🇳🇴",
    "arabic": "🇸🇦",
    "turkish": "🇹🇷",
    "vietnamese": "🇻🇳",
    "indonesian": "🇮🇩",
    "thai": "🇹🇭",
    "malay": "🇲🇾",
    "hebrew": "🇮🇱",
    "persian": "🇮🇷",
    "bengali": "🇧🇩",
}


def get_language_emoji(language: str):
    language_formatted = language.replace(" ", "_").lower()
    return (
        languages_emojis[language_formatted]
        if language_formatted in languages_emojis
        else language
    )


translation_table = {
    "ā": "a",
    "ă": "a",
    "ą": "a",
    "ć": "c",
    "č": "c",
    "ç": "c",
    "ĉ": "c",
    "ċ": "c",
    "ď": "d",
    "đ": "d",
    "è": "e",
    "é": "e",
    "ê": "e",
    "ë": "e",
    "ē": "e",
    "ĕ": "e",
    "ę": "e",
    "ě": "e",
    "ĝ": "g",
    "ğ": "g",
    "ġ": "g",
    "ģ": "g",
    "ĥ": "h",
    "î": "i",
    "ï": "i",
    "ì": "i",
    "í": "i",
    "ī": "i",
    "ĩ": "i",
    "ĭ": "i",
    "ı": "i",
    "ĵ": "j",
    "ķ": "k",
    "ĺ": "l",
    "ļ": "l",
    "ł": "l",
    "ń": "n",
    "ň": "n",
    "ñ": "n",
    "ņ": "n",
    "ŉ": "n",
    "ó": "o",
    "ô": "o",
    "õ": "o",
    "ö": "o",
    "ø": "o",
    "ō": "o",
    "ő": "o",
    "œ": "oe",
    "ŕ": "r",
    "ř": "r",
    "ŗ": "r",
    "š": "s",
    "ş": "s",
    "ś": "s",
    "ș": "s",
    "ß": "ss",
    "ť": "t",
    "ţ": "t",
    "ū": "u",
    "ŭ": "u",
    "ũ": "u",
    "û": "u",
    "ü": "u",
    "ù": "u",
    "ú": "u",
    "ų": "u",
    "ű": "u",
    "ŵ": "w",
    "ý": "y",
    "ÿ": "y",
    "ŷ": "y",
    "ž": "z",
    "ż": "z",
    "ź": "z",
    "æ": "ae",
    "ǎ": "a",
    "ǧ": "g",
    "ə": "e",
    "ƒ": "f",
    "ǐ": "i",
    "ǒ": "o",
    "ǔ": "u",
    "ǚ": "u",
    "ǜ": "u",
    "ǹ": "n",
    "ǻ": "a",
    "ǽ": "ae",
    "ǿ": "o",
}

translation_table = str.maketrans(translation_table)
info_hash_pattern = re.compile(r"\b([a-fA-F0-9]{40})\b")


def translate(title: str):
    return title.translate(translation_table)


def is_video(title: str):
    return title.endswith(
        tuple(
            [
                ".mkv",
                ".mp4",
                ".avi",
                ".mov",
                ".flv",
                ".wmv",
                ".webm",
                ".mpg",
                ".mpeg",
                ".m4v",
                ".3gp",
                ".3g2",
                ".ogv",
                ".ogg",
                ".drc",
                ".gif",
                ".gifv",
                ".mng",
                ".avi",
                ".mov",
                ".qt",
                ".wmv",
                ".yuv",
                ".rm",
                ".rmvb",
                ".asf",
                ".amv",
                ".m4p",
                ".m4v",
                ".mpg",
                ".mp2",
                ".mpeg",
                ".mpe",
                ".mpv",
                ".mpg",
                ".mpeg",
                ".m2v",
                ".m4v",
                ".svi",
                ".3gp",
                ".3g2",
                ".mxf",
                ".roq",
                ".nsv",
                ".flv",
                ".f4v",
                ".f4p",
                ".f4a",
                ".f4b",
            ]
        )
    )


def bytes_to_size(bytes: int):
    sizes = ["Bytes", "KB", "MB", "GB", "TB"]
    if bytes == 0:
        return "0 Byte"

    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024
        i += 1

    return f"{round(bytes, 2)} {sizes[i]}"


def config_check(b64config: str):
    try:
        config = json.loads(base64.b64decode(b64config).decode())
        validated_config = ConfigModel(**config)
        return validated_config.model_dump()
    except:
        return False


def get_debrid_extension(debridService: str):
    debrid_extension = None
    if debridService == "realdebrid":
        debrid_extension = "RD"
    elif debridService == "alldebrid":
        debrid_extension = "AD"
    elif debridService == "premiumize":
        debrid_extension = "PM"
    elif debridService == "torbox":
        debrid_extension = "TB"
    elif debridService == "debridlink":
        debrid_extension = "DL"

    return debrid_extension


async def get_indexer_manager(
    session: aiohttp.ClientSession,
    indexer_manager_type: str,
    indexers: list,
    query: str,
):
    results = []
    try:
        indexers = [indexer.replace("_", " ") for indexer in indexers]
        timeout = aiohttp.ClientTimeout(total=settings.INDEXER_MANAGER_TIMEOUT)

        if indexer_manager_type == "jackett":
            response = await session.get(
                f"{settings.INDEXER_MANAGER_URL}/api/v2.0/indexers/all/results?apikey={settings.INDEXER_MANAGER_API_KEY}&Query={query}&Tracker[]={'&Tracker[]='.join(indexer for indexer in indexers)}",
                timeout=timeout,
            )
            response = await response.json()

            for result in response["Results"]:
                results.append(result)

        if indexer_manager_type == "prowlarr":
            get_indexers = await session.get(
                f"{settings.INDEXER_MANAGER_URL}/api/v1/indexer",
                headers={"X-Api-Key": settings.INDEXER_MANAGER_API_KEY},
            )
            get_indexers = await get_indexers.json()

            indexers_id = []
            for indexer in get_indexers:
                if (
                    indexer["name"].lower() in indexers
                    or indexer["definitionName"].lower() in indexers
                ):
                    indexers_id.append(indexer["id"])

            response = await session.get(
                f"{settings.INDEXER_MANAGER_URL}/api/v1/search?query={query}&indexerIds={'&indexerIds='.join(str(indexer_id) for indexer_id in indexers_id)}&type=search",
                headers={"X-Api-Key": settings.INDEXER_MANAGER_API_KEY},
            )
            response = await response.json()

            for result in response:
                result["InfoHash"] = (
                    result["infoHash"] if "infoHash" in result else None
                )
                result["Title"] = result["title"]
                result["Size"] = result["size"]
                result["Link"] = (
                    result["downloadUrl"] if "downloadUrl" in result else None
                )
                result["Tracker"] = result["indexer"]

                results.append(result)
    except Exception as e:
        logger.warning(
            f"Exception while getting {indexer_manager_type} results for {query} with {indexers}: {e}"
        )
        pass

    return results


async def get_zilean(
    session: aiohttp.ClientSession, name: str, log_name: str, season: int, episode: int
):
    results = []
    try:
        if not season:
            get_dmm = await session.post(
                f"{settings.ZILEAN_URL}/dmm/search", json={"queryText": name}
            )
            get_dmm = await get_dmm.json()

            if isinstance(get_dmm, list):
                take_first = get_dmm[: settings.ZILEAN_TAKE_FIRST]
                for result in take_first:
                    object = {
                        "Title": result["raw_title"],
                        "InfoHash": result["info_hash"],
                        "Size": result["size"],
                        "Tracker": "DMM",
                    }

                    results.append(object)
        else:
            get_dmm = await session.get(
                f"{settings.ZILEAN_URL}/dmm/filtered?query={name}&season={season}&episode={episode}"
            )
            get_dmm = await get_dmm.json()

            if isinstance(get_dmm, list):
                take_first = get_dmm[: settings.ZILEAN_TAKE_FIRST]
                for result in take_first:
                    object = {
                        "Title": result["raw_title"],
                        "InfoHash": result["info_hash"],
                        "Size": result["size"],
                        "Tracker": "DMM",
                    }

                    results.append(object)

        logger.info(f"{len(results)} torrents found for {log_name} with Zilean")
    except Exception as e:
        logger.warning(
            f"Exception while getting torrents for {log_name} with Zilean: {e}"
        )
        pass

    return results


async def get_torrentio(log_name: str, type: str, full_id: str):
    results = []
    try:
        try:
            get_torrentio = requests.get(
                f"https://torrentio.strem.fun/stream/{type}/{full_id}.json"
            ).json()
        except:
            get_torrentio = requests.get(
                f"https://torrentio.strem.fun/stream/{type}/{full_id}.json",
                proxies={
                    "http": settings.DEBRID_PROXY_URL,
                    "https": settings.DEBRID_PROXY_URL,
                },
            ).json()

        for torrent in get_torrentio["streams"]:
            title = torrent["title"]
            title_full = title.split("\n👤")[0]
            tracker = title.split("⚙️ ")[1].split("\n")[0]

            results.append(
                {
                    "Title": title_full,
                    "InfoHash": torrent["infoHash"],
                    "Size": None,
                    "Tracker": f"Torrentio|{tracker}",
                }
            )

        logger.info(f"{len(results)} torrents found for {log_name} with Torrentio")
    except Exception as e:
        logger.warning(
            f"Exception while getting torrents for {log_name} with Torrentio, your IP is most likely blacklisted (you should try proxying Comet): {e}"
        )
        pass

    return results


async def filter(torrents: list, name: str):
    results = []
    for torrent in torrents:
        index = torrent[0]
        title = torrent[1]

        if "\n" in title:  # Torrentio title parsing
            title = title.split("\n")[1]

        if title_match(name, parse(title).parsed_title):
            results.append((index, True))
            continue

        results.append((index, False))

    return results


async def add_uncached_files(
        files: dict,
        torrents: list,
        cache_key: str,
        log_name: str,
        allowed_tracker_ids: list,
        config: dict,
        database: Database
):
    max_index = max((int(files[key]["index"]) for key in files if files[key]["index"] is not None), default=0)
    max_uncached = config.get("maxUncached", 0)
    tracker_key = "Tracker" if settings.INDEXER_MANAGER_TYPE == 'prowlarr' else "TrackerId"
    allowed_tracker_ids = [tracker_id.lower() for tracker_id in allowed_tracker_ids]
    uncached_torrent_list = []
    uncached_torrents = []

    for torrent in torrents:
        tracker = torrent.get(tracker_key, "").lower()
        if tracker in allowed_tracker_ids:
            info_hash = torrent["InfoHash"]
            if info_hash not in files:
                torrent_data = {
                    "index": str(max_index + 1),
                    "title": torrent["Title"],
                    "size": torrent["Size"],
                    "uncached": True,
                    "link": torrent["Link"],
                    "seeders": torrent.get("Seeders", 0)
                }
                uncached_torrent_list.append((info_hash, torrent_data))
                max_index += 1

    # Sort the uncached torrents by seeders in descending order
    uncached_torrent_list.sort(key=lambda x: x[1]["seeders"], reverse=True)

    # If max_uncached is greater than 0, limit the number of uncached torrents
    if max_uncached > 0:
        uncached_torrent_list = uncached_torrent_list[:max_uncached]

    # Add the sorted and filtered uncached torrents to the files dict
    for info_hash, torrent_data in uncached_torrent_list:
        files[info_hash] = torrent_data

        uncached_torrents.append({
            "hash": info_hash,
            "torrentId": "",
            "data": json.dumps(torrent_data),
            "cacheKey": cache_key
        })

    # Perform batch insert of uncached torrents into the database
    if uncached_torrents:
        await database.execute_many(
            "INSERT OR REPLACE INTO uncached_torrents (hash, torrentId, data, cacheKey) VALUES (:hash, :torrentId, :data, :cacheKey)",
            uncached_torrents
        )

    length_uncached = sum(
        1 for file in files.values() if file.get("uncached", False)
    )
    logger.info(
        f"{length_uncached} uncached files found on {allowed_tracker_ids} for {log_name}"
    )


async def get_torrent_hash(session: aiohttp.ClientSession, torrent: tuple):
    index = torrent[0]
    torrent = torrent[1]
    if "InfoHash" in torrent and torrent["InfoHash"] is not None:
        return (index, torrent["InfoHash"].lower())

    url = torrent["Link"]

    try:
        timeout = aiohttp.ClientTimeout(total=settings.GET_TORRENT_TIMEOUT)
        response = await session.get(url, allow_redirects=False, timeout=timeout)
        if response.status == 200:
            torrent_data = await response.read()
            torrent_dict = bencodepy.decode(torrent_data)
            info = bencodepy.encode(torrent_dict[b"info"])
            hash = hashlib.sha1(info).hexdigest()
        else:
            location = response.headers.get("Location", "")
            if not location:
                return (index, None)

            match = info_hash_pattern.search(location)
            if not match:
                return (index, None)

            hash = match.group(1).upper()

        return (index, hash.lower())
    except Exception as e:
        logger.warning(
            f"Exception while getting torrent info hash for {torrent['indexer'] if 'indexer' in torrent else (torrent['Tracker'] if 'Tracker' in torrent else '')}|{url}: {e}"
        )

        return (index, None)


def get_balanced_hashes(hashes: dict, config: dict):
    max_results = config["maxResults"]
    max_size = config["maxSize"]
    config_resolutions = config["resolutions"]
    config_resolutions_order = config.get("resolutionsOrder", [])
    config_languages = {
        language.replace("_", " ").capitalize() for language in config["languages"]
    }
    config_language_preference = {
        language.replace("_", " ").capitalize() for language in config["languagePreference"]
    }
    include_all_languages = "All" in config_languages
    include_all_resolutions = "All" in config_resolutions
    include_unknown_resolution = (
        include_all_resolutions or "Unknown" in config_resolutions
    )

    hashes_by_resolution = {}
    for hash, hash_data in hashes.items():
        hash_info = hash_data["data"]

        if max_size != 0 and hash_info["size"] > max_size:
            continue

        if (
            not include_all_languages
            and not hash_info["is_multi_audio"]
            and not any(lang in hash_info["language"] for lang in config_languages)
        ):
            continue

        resolution = hash_info["resolution"]
        if not resolution:
            if not include_unknown_resolution:
                continue
            resolution_key = "Unknown"
        else:
            resolution_key = resolution[0]
            if not include_all_resolutions and resolution_key not in config_resolutions:
                continue
        if "Uncached" in config["resolutionsOrder"] and "Sort_by_Rank" not in config["sortType"]:
            if hash_info.get("uncached", False):
                resolution_key = "Uncached"
        if resolution_key not in hashes_by_resolution:
            hashes_by_resolution[resolution_key] = []
        hashes_by_resolution[resolution_key].append(hash)

    # Sorting
    hashes_by_resolution = apply_sorting(hashes_by_resolution, hashes, config_resolutions_order, config_language_preference,config.get("sortType", "Sort_by_Rank"))

    total_resolutions = len(hashes_by_resolution)
    if max_results == 0 or total_resolutions == 0:
        return hashes_by_resolution

    hashes_per_resolution = max_results // total_resolutions
    extra_hashes = max_results % total_resolutions

    balanced_hashes = {}
    for resolution, hash_list in hashes_by_resolution.items():
        selected_count = hashes_per_resolution + (1 if extra_hashes > 0 else 0)
        balanced_hashes[resolution] = hash_list[:selected_count]
        if extra_hashes > 0:
            extra_hashes -= 1

    selected_total = sum(len(hashes) for hashes in balanced_hashes.values())
    if selected_total < max_results:
        missing_hashes = max_results - selected_total
        for resolution, hash_list in hashes_by_resolution.items():
            if missing_hashes <= 0:
                break
            current_count = len(balanced_hashes[resolution])
            available_hashes = hash_list[current_count : current_count + missing_hashes]
            balanced_hashes[resolution].extend(available_hashes)
            missing_hashes -= len(available_hashes)

    return balanced_hashes


def apply_sorting(hashes_by_resolution, hashes, config_resolutions_order, config_languages_preference, sort_type):
    """Apply the specified sorting function based on the sort_type string."""
    def sort_by_resolution(res):
        """Sort by resolution based on the config order."""
        try:
            return config_resolutions_order.index(res)
        except ValueError:
            return len(config_resolutions_order)

    def sort_by_priority_language(hash_key):
        """Sort by priority language based on config_languages_priority."""
        languages = hashes[hash_key]["data"].get("language", [])
        for i, lang in enumerate(config_languages_preference):
            if lang in languages:
                return i
        return len(config_languages_preference)

    def sort_by_resolution_only():
        """Sort by resolution based on the config order and sort Uncached by seeders."""
        sorted_hashes_by_resolution = dict(
            sorted(hashes_by_resolution.items(), key=lambda item: sort_by_resolution(item[0]))
        )
        return sort_uncached_by_seeders(sorted_hashes_by_resolution)

    def sort_by_resolution_then_seeders():
        """Sort by resolution, then by seeders within each resolution."""
        sorted_hashes_by_resolution = dict(
            sorted(hashes_by_resolution.items(), key=lambda item: sort_by_resolution(item[0]))
        )
        for res, hash_list in sorted_hashes_by_resolution.items():
            hash_list.sort(
                key=lambda hash_key: -(
                    int(hashes[hash_key]["data"].get("seeders", 0)) if hashes[hash_key]["data"].get(
                        "seeders") != "?" else 0
                )
            )
        return sort_uncached_by_seeders(sorted_hashes_by_resolution)

    def sort_by_resolution_then_size():
        """Sort by resolution, then by file size within each resolution."""
        sorted_hashes_by_resolution = dict(
            sorted(hashes_by_resolution.items(), key=lambda item: sort_by_resolution(item[0]))
        )
        for res, hash_list in sorted_hashes_by_resolution.items():
            hash_list.sort(
                key=lambda hash_key: -hashes[hash_key]["data"].get("size", 0)
            )
        return sort_uncached_by_seeders(sorted_hashes_by_resolution)

    def sort_uncached_by_seeders(sorted_hashes_by_resolution: dict):
        """Sort Uncached, if Uncached Key exists, by seeders."""
        if "Uncached" in sorted_hashes_by_resolution:
            sorted_hashes_by_resolution["Uncached"].sort(
                key=lambda hash_key: -(
                    int(hashes[hash_key]["data"].get("seeders", 0)) if hashes[hash_key]["data"].get(
                        "seeders") != "?" else 0
                )
            )
        return sorted_hashes_by_resolution

    def prioritize_languages(sorted_hashes_by_resolution: dict):
        """Prioritize torrents by languages according to config_languages_priority."""
        for res, hash_list in sorted_hashes_by_resolution.items():
            prioritized = []
            non_prioritized = []
            for hash_key in hash_list:
                if any(lang in hashes[hash_key]["data"].get("language", []) for lang in config_languages_preference):
                    prioritized.append(hash_key)
                else:
                    non_prioritized.append(hash_key)

            # Sort the prioritized list by the language priority order
            prioritized.sort(key=sort_by_priority_language)

            # Merge the prioritized and non-prioritized lists, keeping the relative order intact
            sorted_hashes_by_resolution[res] = prioritized + non_prioritized
        return sorted_hashes_by_resolution

    # If no resolution order is provided, use default.
    if not config_resolutions_order:
        config_resolutions_order = [
            "4K",
            "2160p",
            "1440p",
            "1080p",
            "720p",
            "576p",
            "480p",
            "360p",
            "Uncached",
            "Unknown",
        ]
    if sort_type == "Sort_by_Rank":
        sorted_hashes_by_resolution = hashes_by_resolution
    elif sort_type == "Sort_by_Resolution":
        sorted_hashes_by_resolution = sort_by_resolution_only()
    elif sort_type == "Sort_by_Resolution_then_Seeders":
        sorted_hashes_by_resolution = sort_by_resolution_then_seeders()
    elif sort_type == "Sort_by_Resolution_then_Size":
        sorted_hashes_by_resolution = sort_by_resolution_then_size()
    else:
        logger.warning(
            f"Invalid sort type, results will be sorted by rank"
        )
        sorted_hashes_by_resolution = hashes_by_resolution
        # Apply language prioritization after the main sorting.
    if config_languages_preference:
        logger.info(f"Sorting results by language Preference {config_languages_preference}")
        sorted_hashes_by_resolution = prioritize_languages(sorted_hashes_by_resolution)
    return sorted_hashes_by_resolution

def format_metadata(data: dict):
    extras = []
    if data["hdr"] != "":
        extras.append(data["hdr"] if data["hdr"] != "DV" else "Dolby Vision")
    if data["remux"]:
        extras.append("Remux")
    if data["proper"]:
        extras.append("Proper")
    if data["repack"]:
        extras.append("Repack")
    if data["upscaled"]:
        extras.append("Upscaled")
    if data["remastered"]:
        extras.append("Remastered")
    if data["directorsCut"]:
        extras.append("Director's Cut")
    if data["extended"]:
        extras.append("Extended")
    return " | ".join(extras)


def format_title(data: dict, config: dict):
    title = ""
    logger.info(config)
    if "Title" in config["resultFormat"] or "All" in config["resultFormat"]:
        title += f"{data['title']}\n"
    if "Metadata" in config["resultFormat"] or "All" in config["resultFormat"]:
        metadata = format_metadata(data)
        if metadata != "":
            title += f"💿 {metadata}\n"
    if "Size" in config["resultFormat"] or "All" in config["resultFormat"]:
        title += f"💾 {bytes_to_size(data['size'])} "
    if "Tracker" in config["resultFormat"] or "All" in config["resultFormat"]:
        title += f"🔎 {data['tracker'] if 'tracker' in data else '?'}"
    if "Uncached" in config["resultFormat"] or "All" in config["resultFormat"]:
        if data.get("uncached", False):
            title += "\n" + f"⚠️ Uncached"
    if "Seeders" in config["resultFormat"] or "All" in config["resultFormat"] or data.get("uncached", True):
        if data.get('seeders') is not None and data.get('seeders') != '?':
            title += f"🌱 {data.get('seeders')} Seeders"
    if "Languages" in config["resultFormat"] or "All" in config["resultFormat"]:
        languages = data["language"]
        formatted_languages = (
            "/".join(get_language_emoji(language) for language in languages)
            if languages
            else get_language_emoji("multi_audio") if data["is_multi_audio"] else None
        )
        languages_str = "\n" + formatted_languages if formatted_languages else ""
        title += f"{languages_str}"
    if title == "":
        # Without this, Streamio shows SD as the result, which is confusing
        title = "Empty result format configuration"
    return title
