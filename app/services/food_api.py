"""
공공데이터포털 식품 API 서비스
- 식품(첨가물)품목제조보고 API
- 식품제조가공업정보 API
- 업체 검색 및 품목 조회
"""
import os
import asyncio
import httpx
from typing import Optional
from pydantic import BaseModel


# 지역 코드 매핑
REGION_CODES = {
    "전체": "",
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주"
}

# 업종 코드 매핑
BUSINESS_TYPES = {
    "전체": "",
    "식품": "식품",
    "건강기능식품": "건강기능식품",
    "음식점": "음식점"
}


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
    api_source: Optional[str] = None


class CompanyItem(BaseModel):
    """업체 정보 모델"""
    company_name: str
    license_no: Optional[str] = None
    business_type: Optional[str] = None
    representative: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    license_date: Optional[str] = None
    api_source: Optional[str] = None


class FoodSearchResult(BaseModel):
    """식품 검색 결과 모델"""
    total_count: int
    page: int
    per_page: int
    items: list[FoodItem]


class CompanySearchResult(BaseModel):
    """업체 검색 결과 모델"""
    total_count: int
    page: int
    per_page: int
    items: list[CompanyItem]


class FoodAPIService:
    """통합 식품 API 서비스"""

    # API 엔드포인트들
    APIS = {
        "food_product": {
            "name": "식품품목제조보고",
            "base_url": "http://apis.data.go.kr/1471000/FoodFlshdAddtvrptInfoService",
            "endpoint": "/getFoodFlshdAddtvrptInfoList",
        },
        "food_manufacture": {
            "name": "식품제조가공업",
            "base_url": "http://apis.data.go.kr/B553748/CertImgListServiceV3",
            "endpoint": "/getCertImgListServiceV3",
        }
    }

    def __init__(self):
        self.api_key_1 = os.getenv("PUBLIC_DATA_API_KEY", "")
        self.api_key_2 = os.getenv("PUBLIC_DATA_API_KEY_2", "")

    async def search_companies(
        self,
        keyword: str = "",
        region: str = "",
        business_type: str = "",
        page: int = 1,
        per_page: int = 10
    ) -> CompanySearchResult:
        """
        업체 검색

        Args:
            keyword: 업체명 키워드
            region: 지역
            business_type: 업종
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            CompanySearchResult: 업체 검색 결과
        """
        if not self.api_key_1:
            return self._get_sample_companies(keyword, region, business_type, page, per_page)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "serviceKey": self.api_key_1,
                    "pageNo": str(page),
                    "numOfRows": str(per_page),
                    "type": "json"
                }

                # 검색 조건 추가
                if keyword:
                    params["BSSH_NM"] = keyword
                if region:
                    params["ADDR"] = region

                api_info = self.APIS["food_product"]
                url = f"{api_info['base_url']}{api_info['endpoint']}"

                response = await client.get(url, params=params)
                print(f"[업체검색] 요청: {response.url}")
                print(f"[업체검색] 상태: {response.status_code}")

                response.raise_for_status()
                data = response.json()

                return self._parse_company_response(data, page, per_page)

        except Exception as e:
            print(f"[업체검색] API 오류: {e}")
            return self._get_sample_companies(keyword, region, business_type, page, per_page)

    async def search_products_by_company(
        self,
        company_name: str,
        page: int = 1,
        per_page: int = 20
    ) -> FoodSearchResult:
        """
        업체별 품목 검색

        Args:
            company_name: 업체명
            page: 페이지 번호
            per_page: 페이지당 결과 수

        Returns:
            FoodSearchResult: 품목 검색 결과
        """
        if not self.api_key_1:
            return self._get_sample_products_by_company(company_name, page, per_page)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "serviceKey": self.api_key_1,
                    "BSSH_NM": company_name,
                    "pageNo": str(page),
                    "numOfRows": str(per_page),
                    "type": "json"
                }

                api_info = self.APIS["food_product"]
                url = f"{api_info['base_url']}{api_info['endpoint']}"

                response = await client.get(url, params=params)
                print(f"[품목검색] 요청: {response.url}")
                print(f"[품목검색] 상태: {response.status_code}")

                response.raise_for_status()
                data = response.json()

                return self._parse_food_product_response(data, page, per_page)

        except Exception as e:
            print(f"[품목검색] API 오류: {e}")
            return self._get_sample_products_by_company(company_name, page, per_page)

    async def search_foods(
        self,
        keyword: str,
        page: int = 1,
        per_page: int = 10
    ) -> FoodSearchResult:
        """제품명으로 식품 검색"""
        if not self.api_key_1 and not self.api_key_2:
            return self._get_sample_data(keyword, page, per_page)

        tasks = []
        if self.api_key_1:
            tasks.append(self._search_food_product(keyword, page, per_page))
        if self.api_key_2:
            tasks.append(self._search_food_manufacture(keyword, page, per_page))

        if not tasks:
            return self._get_sample_data(keyword, page, per_page)

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_items = []
            total_count = 0

            for result in results:
                if isinstance(result, FoodSearchResult):
                    all_items.extend(result.items)
                    total_count += result.total_count
                elif isinstance(result, Exception):
                    print(f"API 호출 오류: {result}")

            if not all_items:
                return self._get_sample_data(keyword, page, per_page)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=all_items[:per_page]
            )

        except Exception as e:
            print(f"통합 검색 오류: {e}")
            return self._get_sample_data(keyword, page, per_page)

    async def _search_food_product(
        self,
        keyword: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """식품품목제조보고 API 검색"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "serviceKey": self.api_key_1,
                    "PRDLST_NM": keyword,
                    "pageNo": str(page),
                    "numOfRows": str(per_page),
                    "type": "json"
                }

                api_info = self.APIS["food_product"]
                url = f"{api_info['base_url']}{api_info['endpoint']}"

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return self._parse_food_product_response(data, page, per_page)

        except Exception as e:
            print(f"[식품품목] API 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_food_manufacture(
        self,
        keyword: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """식품제조가공업 API 검색"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "serviceKey": self.api_key_2,
                    "prdlstNm": keyword,
                    "pageNo": str(page),
                    "numOfRows": str(per_page),
                    "returnType": "json"
                }

                api_info = self.APIS["food_manufacture"]
                url = f"{api_info['base_url']}{api_info['endpoint']}"

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return self._parse_food_manufacture_response(data, page, per_page)

        except Exception as e:
            print(f"[식품제조] API 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_company_response(
        self,
        data: dict,
        page: int,
        per_page: int
    ) -> CompanySearchResult:
        """업체 API 응답 파싱"""
        try:
            body = data.get("body", {})
            total_count = body.get("totalCount", 0)
            items_data = body.get("items", [])

            if not items_data:
                return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            # 업체명으로 그룹화 (중복 제거)
            companies_dict = {}
            for item in items_data:
                company_name = item.get("BSSH_NM", "")
                if company_name and company_name not in companies_dict:
                    companies_dict[company_name] = CompanyItem(
                        company_name=company_name,
                        license_no=item.get("PRDLST_REPORT_NO", ""),
                        business_type=item.get("PRDLST_DCNM", "식품"),
                        address=item.get("ADDR", "") or item.get("SITE_ADDR", ""),
                        status="운영",
                        api_source="식품품목제조보고"
                    )

            items = list(companies_dict.values())

            return CompanySearchResult(
                total_count=len(items),
                page=page,
                per_page=per_page,
                items=items[:per_page]
            )
        except Exception as e:
            print(f"[업체] 파싱 오류: {e}")
            return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_food_product_response(
        self,
        data: dict,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """식품품목제조보고 API 응답 파싱"""
        try:
            body = data.get("body", {})
            total_count = body.get("totalCount", 0)
            items_data = body.get("items", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food_item = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDT_SHAP_CD_NM", "") or item.get("PRDLST_DCNM", ""),
                    serving_size=item.get("CSTDY_MTHD", ""),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    raw_materials=item.get("RAWMTRL_NM", ""),
                    api_source="식품품목제조보고"
                )
                items.append(food_item)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[식품품목] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_food_manufacture_response(
        self,
        data: dict,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """식품제조가공업 API 응답 파싱"""
        try:
            body = data.get("body", {})
            total_count = body.get("totalCount", 0)
            items_data = body.get("items", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food_item = FoodItem(
                    food_name=item.get("prdlstNm", ""),
                    food_code=item.get("prdlstReportNo", ""),
                    category=item.get("prdkind", ""),
                    manufacturer=item.get("manufacture", ""),
                    report_no=item.get("prdlstReportNo", ""),
                    raw_materials=item.get("rawmtrl", ""),
                    calories=self._safe_float(item.get("kcal")),
                    carbohydrate=self._safe_float(item.get("carbo")),
                    protein=self._safe_float(item.get("protein")),
                    fat=self._safe_float(item.get("fat")),
                    sugar=self._safe_float(item.get("sugar")),
                    sodium=self._safe_float(item.get("natrium")),
                    serving_size=item.get("capacity", ""),
                    api_source="식품안전나라"
                )
                items.append(food_item)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[식품제조] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _safe_float(self, value) -> Optional[float]:
        """안전한 float 변환"""
        if value is None or value == "":
            return None
        try:
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _get_sample_companies(
        self,
        keyword: str,
        region: str,
        business_type: str,
        page: int,
        per_page: int
    ) -> CompanySearchResult:
        """샘플 업체 데이터"""
        sample_companies = [
            CompanyItem(
                company_name="삼양식품(주)",
                license_no="19670001",
                business_type="식품",
                address="서울특별시 성북구 삼양로 123",
                region="서울",
                status="운영",
                license_date="1967-01-01",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="농심(주)",
                license_no="19680002",
                business_type="식품",
                address="서울특별시 동작구 신대방동 456",
                region="서울",
                status="운영",
                license_date="1968-03-15",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="오뚜기(주)",
                license_no="19690003",
                business_type="식품",
                address="경기도 안양시 동안구",
                region="경기",
                status="운영",
                license_date="1969-05-20",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="CJ제일제당(주)",
                license_no="19530004",
                business_type="식품",
                address="서울특별시 중구",
                region="서울",
                status="운영",
                license_date="1953-08-01",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="대상(주)",
                license_no="19560005",
                business_type="식품",
                address="서울특별시 종로구",
                region="서울",
                status="운영",
                license_date="1956-12-10",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="풀무원식품(주)",
                license_no="19840006",
                business_type="식품",
                address="서울특별시 강남구",
                region="서울",
                status="운영",
                license_date="1984-06-01",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="빙그레(주)",
                license_no="19670007",
                business_type="식품",
                address="경기도 남양주시",
                region="경기",
                status="운영",
                license_date="1967-09-15",
                api_source="샘플데이터"
            ),
            CompanyItem(
                company_name="롯데제과(주)",
                license_no="19670008",
                business_type="식품",
                address="서울특별시 영등포구",
                region="서울",
                status="운영",
                license_date="1967-04-01",
                api_source="샘플데이터"
            ),
        ]

        # 필터링
        filtered = sample_companies
        if keyword:
            filtered = [c for c in filtered if keyword.lower() in c.company_name.lower()]
        if region:
            filtered = [c for c in filtered if region in (c.region or "") or region in (c.address or "")]
        if business_type:
            filtered = [c for c in filtered if business_type in (c.business_type or "")]

        # 페이지네이션
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]

        return CompanySearchResult(
            total_count=len(filtered),
            page=page,
            per_page=per_page,
            items=paginated
        )

    def _get_sample_products_by_company(
        self,
        company_name: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """샘플 업체별 품목 데이터"""
        sample_products = {
            "농심(주)": [
                FoodItem(food_name="신라면", category="라면", manufacturer="농심(주)", report_no="NM001", api_source="샘플데이터"),
                FoodItem(food_name="안성탕면", category="라면", manufacturer="농심(주)", report_no="NM002", api_source="샘플데이터"),
                FoodItem(food_name="짜파게티", category="라면", manufacturer="농심(주)", report_no="NM003", api_source="샘플데이터"),
                FoodItem(food_name="너구리", category="라면", manufacturer="농심(주)", report_no="NM004", api_source="샘플데이터"),
                FoodItem(food_name="새우깡", category="스낵", manufacturer="농심(주)", report_no="NM005", api_source="샘플데이터"),
            ],
            "삼양식품(주)": [
                FoodItem(food_name="삼양라면", category="라면", manufacturer="삼양식품(주)", report_no="SY001", api_source="샘플데이터"),
                FoodItem(food_name="불닭볶음면", category="라면", manufacturer="삼양식품(주)", report_no="SY002", api_source="샘플데이터"),
                FoodItem(food_name="짜짜로니", category="라면", manufacturer="삼양식품(주)", report_no="SY003", api_source="샘플데이터"),
            ],
            "오뚜기(주)": [
                FoodItem(food_name="진라면", category="라면", manufacturer="오뚜기(주)", report_no="OT001", api_source="샘플데이터"),
                FoodItem(food_name="참깨라면", category="라면", manufacturer="오뚜기(주)", report_no="OT002", api_source="샘플데이터"),
                FoodItem(food_name="오뚜기카레", category="즉석조리식품", manufacturer="오뚜기(주)", report_no="OT003", api_source="샘플데이터"),
            ],
        }

        items = sample_products.get(company_name, [])

        return FoodSearchResult(
            total_count=len(items),
            page=page,
            per_page=per_page,
            items=items
        )

    def _get_sample_data(
        self,
        keyword: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """샘플 식품 데이터"""
        sample_foods = [
            FoodItem(food_name="현미밥", category="밥류", manufacturer="일반", api_source="샘플데이터",
                     calories=313.0, carbohydrate=68.5, protein=6.5, fat=1.2),
            FoodItem(food_name="김치찌개", category="찌개류", manufacturer="일반", api_source="샘플데이터",
                     calories=156.0, carbohydrate=8.2, protein=12.5, fat=9.8),
            FoodItem(food_name="라면", category="면류", manufacturer="농심", api_source="샘플데이터",
                     calories=500.0, carbohydrate=78.0, protein=10.5, fat=16.0),
        ]

        if keyword:
            filtered = [f for f in sample_foods if keyword.lower() in f.food_name.lower()]
        else:
            filtered = sample_foods

        return FoodSearchResult(
            total_count=len(filtered),
            page=page,
            per_page=per_page,
            items=filtered
        )


# 지역 목록 반환
def get_regions():
    return list(REGION_CODES.keys())

def get_business_types():
    return list(BUSINESS_TYPES.keys())


# 싱글톤 인스턴스
food_api_service = FoodAPIService()
