"""
YouTube Data API Client
- 트렌드 데이터 수집
- 인기 영상 정보 조회
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("google-api-python-client not installed. YouTube API disabled.")


class YouTubeClient:
    """
    YouTube Data API v3 클라이언트
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not YOUTUBE_AVAILABLE:
            raise ImportError("google-api-python-client is required. pip install google-api-python-client")
        
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not found in environment")
        
        self.youtube = build("youtube", "v3", developerKey=self.api_key) if self.api_key else None
    
    async def get_trending_videos(
        self,
        region_code: str = "KR",
        category_id: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        트렌딩 비디오 목록 조회
        
        Args:
            region_code: 국가 코드 (KR, US, JP 등)
            category_id: 카테고리 ID (옵션)
            max_results: 최대 결과 수
        
        Returns:
            List of video data
        """
        if not self.youtube:
            logger.error("YouTube API not initialized")
            return []
        
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                chart="mostPopular",
                regionCode=region_code,
                videoCategoryId=category_id,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                video_data = {
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "view_count": int(item["statistics"].get("viewCount", 0)),
                    "like_count": int(item["statistics"].get("likeCount", 0)),
                    "comment_count": int(item["statistics"].get("commentCount", 0)),
                    "duration": item["contentDetails"]["duration"],
                    "tags": item["snippet"].get("tags", []),
                    "category_id": item["snippet"]["categoryId"]
                }
                videos.append(video_data)
            
            logger.info(f"✅ Fetched {len(videos)} trending videos from YouTube")
            return videos
            
        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch trending videos: {e}")
            return []
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 20,
        order: str = "relevance",  # relevance, date, viewCount, rating
        region_code: str = "KR"
    ) -> List[Dict]:
        """
        키워드로 비디오 검색
        
        Args:
            query: 검색 키워드
            max_results: 최대 결과 수
            order: 정렬 방식
            region_code: 지역 코드
        
        Returns:
            List of video data
        """
        if not self.youtube:
            logger.error("YouTube API not initialized")
            return []
        
        try:
            # 검색 요청
            search_request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order=order,
                regionCode=region_code
            )
            search_response = search_request.execute()
            
            # 비디오 ID 추출
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            
            if not video_ids:
                return []
            
            # 비디오 상세 정보 조회
            videos_request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            )
            videos_response = videos_request.execute()
            
            videos = []
            for item in videos_response.get("items", []):
                video_data = {
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "view_count": int(item["statistics"].get("viewCount", 0)),
                    "like_count": int(item["statistics"].get("likeCount", 0)),
                    "comment_count": int(item["statistics"].get("commentCount", 0)),
                    "duration": item["contentDetails"]["duration"],
                    "tags": item["snippet"].get("tags", []),
                    "category_id": item["snippet"]["categoryId"]
                }
                videos.append(video_data)
            
            logger.info(f"✅ Searched {len(videos)} videos for query: {query}")
            return videos
            
        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to search videos: {e}")
            return []
    
    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        비디오 댓글 조회
        
        Args:
            video_id: YouTube 비디오 ID
            max_results: 최대 댓글 수
        
        Returns:
            List of comments
        """
        if not self.youtube:
            logger.error("YouTube API not initialized")
            return []
        
        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                order="relevance"
            )
            response = request.execute()
            
            comments = []
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": comment["textDisplay"],
                    "author": comment["authorDisplayName"],
                    "like_count": comment["likeCount"],
                    "published_at": comment["publishedAt"]
                })
            
            logger.info(f"✅ Fetched {len(comments)} comments for video: {video_id}")
            return comments
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Comments disabled for video: {video_id}")
            else:
                logger.error(f"❌ YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch comments: {e}")
            return []
