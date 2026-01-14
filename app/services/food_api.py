"""
공공데이터포털 식품 API 서비스
- 식품의약품안전처 식품(첨가물)품목제조보고 API 활용
"""
import os
import httpx
from typing import Optional
from urllib.parse import unquote
from pydantic import BaseModel


class FoodItem(BaseModel):
    """식품 정보 모델"""
    food_name: str
    food_code: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[str] = None
    calories: Optional[float] = None
    carbohydrate: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    manufacturer: Optional[str] = None
    report_no: Optional[str] = None
    raw_materials: Optional[str] = None


class FoodSearchResult(BaseModel):
    """검색 결과 모델"""
    total_count: int
    page: int
    per_page: int
    items: list[FoodItem]


class FoodAPIService:
    """식품 품목제조보고 API 서비스"""

    # 식품(첨가물)품목제조보고(원재료) API
    BASE_URL = "http://apis.data.go.kr/1471000/FoodFlshdAddtvrptInfoService"

    def __init__(self):
        self.api_key = os.getenv("PUBLIC_DATA_API_KEY", "")

    async def search_foods(
        self,
        keyword: str,
        page: int = 1,
        per_page: int = 10
    ) -> FoodSearchResult:
        """
        식품 검색

        Args:
            keyword: 검색 키워드 (제품명)
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            FoodSearchResult: 검색 결과
        """
        if not self.api_key:
            return self._get_sample_data(keyword, page, per_page)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # API 키가 이미 인코딩되어 있으면 그대로 사용
                params = {
                    "serviceKey": self.api_key,
                    "PRDLST_NM": keyword,
                    "pageNo": str(page),
                    "numOfRows": str(per_page),
                    "type": "json"
                }

                response = await client.get(
                    f"{self.BASE_URL}/getFoodFlshdAddtvrptInfoList",
                    params=params
                )

                print(f"API 요청 URL: {response.url}")
                print(f"응답 상태: {response.status_code}")

                response.raise_for_status()
                data = response.json()
                print(f"응답 데이터: {data}")

                return self._parse_api_response(data, page, per_page)

        except Exception as e:
            print(f"API 호출 오류: {e}")
            return self._get_sample_data(keyword, page, per_page)

    def _parse_api_response(
        self,
        data: dict,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """API 응답 파싱"""
        try:
            body = data.get("body", {})
            total_count = body.get("totalCount", 0)
            items_data = body.get("items", [])

            # items가 None이거나 빈 문자열인 경우 처리
            if not items_data:
                return FoodSearchResult(
                    total_count=0,
                    page=page,
                    per_page=per_page,
                    items=[]
                )

            # items가 단일 객체인 경우 리스트로 변환
            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food_item = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDT_SHAP_CD_NM", ""),
                    serving_size=item.get("CSTDY_MTHD", ""),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    raw_materials=item.get("RAWMTRL_NM", ""),
                    calories=None,
                    carbohydrate=None,
                    protein=None,
                    fat=None,
                    sugar=None,
                    sodium=None
                )
                items.append(food_item)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"응답 파싱 오류: {e}")
            return FoodSearchResult(
                total_count=0,
                page=page,
                per_page=per_page,
                items=[]
            )

    def _safe_float(self, value) -> Optional[float]:
        """안전한 float 변환"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_sample_data(
        self,
        keyword: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """샘플 데이터 반환 (API 키 없을 경우 데모용)"""
        sample_foods = [
            FoodItem(
                food_name="현미밥",
                food_code="D000001",
                category="밥류",
                serving_size="210g",
                calories=313.0,
                carbohydrate=68.5,
                protein=6.5,
                fat=1.2,
                sugar=0.5,
                sodium=5.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="김치찌개",
                food_code="D000002",
                category="찌개류",
                serving_size="300g",
                calories=156.0,
                carbohydrate=8.2,
                protein=12.5,
                fat=9.8,
                sugar=2.1,
                sodium=1250.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="된장찌개",
                food_code="D000003",
                category="찌개류",
                serving_size="300g",
                calories=98.0,
                carbohydrate=9.5,
                protein=7.2,
                fat=4.3,
                sugar=1.8,
                sodium=980.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="삼겹살 구이",
                food_code="D000004",
                category="육류구이",
                serving_size="100g",
                calories=331.0,
                carbohydrate=0.0,
                protein=17.5,
                fat=29.1,
                sugar=0.0,
                sodium=58.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="비빔밥",
                food_code="D000005",
                category="밥류",
                serving_size="400g",
                calories=560.0,
                carbohydrate=85.2,
                protein=15.8,
                fat=16.5,
                sugar=8.2,
                sodium=820.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="라면",
                food_code="D000006",
                category="면류",
                serving_size="120g",
                calories=500.0,
                carbohydrate=78.0,
                protein=10.5,
                fat=16.0,
                sugar=4.0,
                sodium=1800.0,
                manufacturer="농심"
            ),
            FoodItem(
                food_name="떡볶이",
                food_code="D000007",
                category="분식류",
                serving_size="250g",
                calories=380.0,
                carbohydrate=72.0,
                protein=8.5,
                fat=7.2,
                sugar=15.0,
                sodium=1100.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="치킨 (후라이드)",
                food_code="D000008",
                category="육류튀김",
                serving_size="150g",
                calories=420.0,
                carbohydrate=18.5,
                protein=28.0,
                fat=26.5,
                sugar=1.2,
                sodium=650.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="김밥",
                food_code="D000009",
                category="밥류",
                serving_size="230g",
                calories=420.0,
                carbohydrate=65.0,
                protein=12.5,
                fat=12.0,
                sugar=5.5,
                sodium=780.0,
                manufacturer="일반"
            ),
            FoodItem(
                food_name="불고기",
                food_code="D000010",
                category="육류볶음",
                serving_size="150g",
                calories=285.0,
                carbohydrate=12.5,
                protein=22.0,
                fat=16.8,
                sugar=8.5,
                sodium=520.0,
                manufacturer="일반"
            ),
        ]

        # 키워드로 필터링
        if keyword:
            filtered = [
                f for f in sample_foods
                if keyword.lower() in f.food_name.lower()
                or keyword.lower() in (f.category or "").lower()
            ]
        else:
            filtered = sample_foods

        # 페이지네이션
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]

        return FoodSearchResult(
            total_count=len(filtered),
            page=page,
            per_page=per_page,
            items=paginated
        )


# 싱글톤 인스턴스
food_api_service = FoodAPIService()
