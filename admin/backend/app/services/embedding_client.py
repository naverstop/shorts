"""
OpenAI Embedding Client
- 텍스트 임베딩 생성
- Vector 유사도 검색
"""
from typing import List, Optional
import numpy as np
from loguru import logger

from app.config import settings

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed. Embedding API disabled.")


class EmbeddingClient:
    """
    OpenAI Embedding 클라이언트
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required.")
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment")
            return
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions
    
    async def create_embedding(
        self,
        text: str
    ) -> Optional[List[float]]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            1536차원 벡터 (List[float])
        """
        if not hasattr(self, 'client'):
            logger.error("OpenAI API not initialized")
            return None
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"✅ Created embedding (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ OpenAI Embedding API error: {e}")
            return None
    
    async def create_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        여러 텍스트의 임베딩 생성 (배치)
        
        Args:
            texts: 임베딩할 텍스트 리스트
        
        Returns:
            임베딩 리스트
        """
        if not hasattr(self, 'client'):
            logger.error("OpenAI API not initialized")
            return [None] * len(texts)
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ OpenAI Embedding API error: {e}")
            return [None] * len(texts)
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        코사인 유사도 계산
        
        Args:
            vec1: 벡터 1
            vec2: 벡터 2
        
        Returns:
            유사도 (0.0 ~ 1.0)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
