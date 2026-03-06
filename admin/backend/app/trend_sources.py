from typing import Any


TREND_SOURCES: list[dict[str, Any]] = [
    {
        "code": "youtube",
        "label": "YouTube",
        "icon": "📺",
        "description": "YouTube 인기 동영상 기반 트렌드",
        "enabled": True,
        "supports_collection": True,
    },
    {
        "code": "youtube_shorts",
        "label": "YouTube Shorts",
        "icon": "🎬",
        "description": "YouTube 인기 영상 중 Shorts 후보(60초 이하) 기반 트렌드",
        "enabled": True,
        "supports_collection": True,
    },
    {
        "code": "tiktok",
        "label": "TikTok",
        "icon": "🎵",
        "description": "TikTok Discover 또는 YouTube 기반 추정 트렌드",
        "enabled": True,
        "supports_collection": True,
    },
]


def get_enabled_trend_source_codes() -> list[str]:
    return [source["code"] for source in TREND_SOURCES if source.get("enabled")]


def get_trend_sources() -> list[dict[str, Any]]:
    return TREND_SOURCES.copy()
