import os

from typing import List, Optional
from databases import Database
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from RTN import RTN, BaseRankingModel, SettingsModel


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ADDON_ID: Optional[str] = "stremio.comet.fast"
    ADDON_NAME: Optional[str] = "Comet"
    FASTAPI_HOST: Optional[str] = "0.0.0.0"
    FASTAPI_PORT: Optional[int] = 8000
    FASTAPI_WORKERS: Optional[int] = 2 * (os.cpu_count() or 1)
    DATABASE_PATH: Optional[str] = "data/comet.db"
    CACHE_TTL: Optional[int] = 86400
    UNCACHED_TTL: Optional[int] = 86400
    DEBRID_PROXY_URL: Optional[str] = None
    INDEXER_MANAGER_TYPE: str = "jackett"
    INDEXER_MANAGER_URL: str = "http://127.0.0.1:9117"
    INDEXER_MANAGER_API_KEY: str
    INDEXER_MANAGER_TIMEOUT: Optional[int] = 30
    INDEXER_MANAGER_INDEXERS: List[str] = ["EXAMPLE1_CHANGETHIS", "EXAMPLE2_CHANGETHIS"]
    GET_TORRENT_TIMEOUT: Optional[int] = 5
    ZILEAN_URL: Optional[str] = None
    ZILEAN_TAKE_FIRST: Optional[int] = 500
    DEBRID_TAKE_FIRST: Optional[int] = 0
    SCRAPE_TORRENTIO: Optional[bool] = False
    CUSTOM_HEADER_HTML: Optional[str] = None
    PROXY_DEBRID_STREAM: Optional[bool] = False
    PROXY_DEBRID_STREAM_PASSWORD: Optional[str] = "CHANGE_ME"
    TITLE_MATCH_CHECK: Optional[bool] = True
    URL_PREFIX: Optional[str] = ""


settings = AppSettings()


class ConfigModel(BaseModel):
    indexers: List[str]
    indexersUncached: List[str]
    languages: Optional[List[str]] = ["All"]
    languagePreference: Optional[List[str]] = []
    searchLanguage: Optional[List[str]] = []
    resolutions: Optional[List[str]] = ["All"]
    resultFormat: Optional[List[str]] = ["All"]
    resolutionsOrder: Optional[List[str]] = []
    enhancedLanguageMatching: Optional[str] = 'False'
    sortType: Optional[str] = 'Sort_by_Rank'
    scrapingPreference: Optional[str] = 'tz'
    maxResults: Optional[int] = 0
    maxSize: Optional[float] = 0
    debridService: str
    debridApiKey: str
    debridStreamProxyPassword: Optional[str] = ""

    @field_validator("indexers")
    def check_indexers(cls, v, values):
        settings.INDEXER_MANAGER_INDEXERS = [
            indexer.replace(" ", "_").lower()
            for indexer in settings.INDEXER_MANAGER_INDEXERS
        ]  # to equal webui
        valid_indexers = [
            indexer for indexer in v if indexer in settings.INDEXER_MANAGER_INDEXERS
        ]
        # if not valid_indexers: # For only Zilean mode
        #     raise ValueError(
        #         f"At least one indexer must be from {settings.INDEXER_MANAGER_INDEXERS}"
        #     )
        return valid_indexers

    @field_validator("indexersUncached")
    def check_indexers(cls, v, values):
        settings.INDEXER_MANAGER_INDEXERS = [
            indexer.replace(" ", "_").lower()
            for indexer in settings.INDEXER_MANAGER_INDEXERS
        ]  # to equal webui
        valid_indexers = [
            indexer for indexer in v if indexer in settings.INDEXER_MANAGER_INDEXERS
        ]
        # if not valid_indexers: # For only Zilean mode
        #     raise ValueError(
        #         f"At least one indexer must be from {settings.INDEXER_MANAGER_INDEXERS}"
        #     )
        return valid_indexers

    @field_validator("maxResults")
    def check_max_results(cls, v):
        if v < 0:
            v = 0
        return v

    @field_validator("maxSize")
    def check_max_size(cls, v):
        if v < 0:
            v = 0
        return v

    @field_validator("debridService")
    def check_debrid_service(cls, v):
        if v not in ["realdebrid", "alldebrid", "premiumize", "torbox", "debridlink"]:
            raise ValueError("Invalid debridService")
        return v


class BestOverallRanking(BaseRankingModel):
    uhd: int = 100
    fhd: int = 90
    hd: int = 80
    sd: int = 70
    dolby_video: int = 100
    hdr: int = 80
    hdr10: int = 90
    dts_x: int = 100
    dts_hd: int = 80
    dts_hd_ma: int = 90
    atmos: int = 90
    truehd: int = 60
    ddplus: int = 40
    aac: int = 30
    ac3: int = 20
    remux: int = 150
    bluray: int = 120
    webdl: int = 90


rtn_settings = SettingsModel()
rtn_ranking = BestOverallRanking()

# For use anywhere
rtn = RTN(settings=rtn_settings, ranking_model=rtn_ranking)
database = Database(f"sqlite:///{settings.DATABASE_PATH}")
