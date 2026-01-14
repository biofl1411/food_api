"""
공공 데이터 식품 검색 플랫폼 API 서버
"""
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

from app.services.food_api import food_api_service, FoodSearchResult

# 환경변수 로드
load_dotenv()

app = FastAPI(
    title="식품 영양정보 검색 플랫폼",
    description="공공데이터포털 API를 활용한 식품 영양성분 검색 서비스",
    version="1.0.0"
)

# 정적 파일 서빙
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    """메인 페이지"""
    return FileResponse(os.path.join(static_path, "index.html"))


@app.get("/api/search", response_model=FoodSearchResult)
async def search_foods(
    q: str = Query(..., min_length=1, description="검색 키워드"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(10, ge=1, le=100, description="페이지당 결과 수")
):
    """
    식품 검색 API

    - **q**: 검색할 식품명 키워드
    - **page**: 페이지 번호 (기본값: 1)
    - **per_page**: 페이지당 결과 수 (기본값: 10, 최대: 100)
    """
    result = await food_api_service.search_foods(
        keyword=q,
        page=page,
        per_page=per_page
    )
    return result


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "food-search-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
