"""
공공 데이터 식품 검색 플랫폼 API 서버
"""
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

from app.services.food_api import (
    food_api_service,
    FoodSearchResult,
    CompanySearchResult,
    get_regions,
    get_business_types
)

# 환경변수 로드
load_dotenv()

app = FastAPI(
    title="식품 업체/품목 검색 플랫폼",
    description="공공데이터포털 API를 활용한 식품 업체 및 품목 검색 서비스",
    version="2.0.0"
)

# 정적 파일 서빙
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    """메인 페이지"""
    return FileResponse(os.path.join(static_path, "index.html"))


@app.get("/api/companies", response_model=CompanySearchResult)
async def search_companies(
    keyword: str = Query("", description="업체명 키워드"),
    region: str = Query("", description="지역"),
    business_type: str = Query("", description="업종"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(10, ge=1, le=100, description="페이지당 결과 수")
):
    """
    업체 검색 API

    - **keyword**: 업체명 키워드
    - **region**: 지역 (서울, 경기 등)
    - **business_type**: 업종 (식품, 건강기능식품 등)
    - **page**: 페이지 번호
    - **per_page**: 페이지당 결과 수
    """
    result = await food_api_service.search_companies(
        keyword=keyword,
        region=region,
        business_type=business_type,
        page=page,
        per_page=per_page
    )
    return result


@app.get("/api/companies/{company_name}/products", response_model=FoodSearchResult)
async def get_company_products(
    company_name: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 결과 수")
):
    """
    업체별 품목 조회 API

    - **company_name**: 업체명
    - **page**: 페이지 번호
    - **per_page**: 페이지당 결과 수
    """
    result = await food_api_service.search_products_by_company(
        company_name=company_name,
        page=page,
        per_page=per_page
    )
    return result


@app.get("/api/search", response_model=FoodSearchResult)
async def search_foods(
    q: str = Query(..., min_length=1, description="검색 키워드"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(10, ge=1, le=100, description="페이지당 결과 수")
):
    """
    식품 검색 API (제품명 검색)

    - **q**: 검색할 식품명 키워드
    - **page**: 페이지 번호
    - **per_page**: 페이지당 결과 수
    """
    result = await food_api_service.search_foods(
        keyword=q,
        page=page,
        per_page=per_page
    )
    return result


@app.get("/api/regions")
async def list_regions():
    """지역 목록 조회"""
    return {"regions": get_regions()}


@app.get("/api/business-types")
async def list_business_types():
    """업종 목록 조회"""
    return {"business_types": get_business_types()}


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "food-search-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1411)
