"""
공공데이터포털 + 식품안전나라 통합 식품 API 서비스
- 공공데이터포털: 식품(첨가물)품목제조보고 API
- 식품안전나라: I1220(식품제조가공업정보), I1250(식품품목제조보고)
- 폴백 구조: 공공데이터포털 실패 시 식품안전나라 API 사용
"""
import os
import httpx
import urllib.parse
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# 환경변수 로드 (싱글톤 생성 전에 호출 필요)
load_dotenv()


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
    "축산": "축산",
    "음식점": "음식점"
}


class FoodItem(BaseModel):
    """식품 정보 모델 (상세 정보 포함)"""
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
    # 상세 정보 (식품안전나라 I1250)
    license_no: Optional[str] = None  # 인허가번호
    permit_date: Optional[str] = None  # 허가일자
    expiry_date: Optional[str] = None  # 소비기한
    shelf_life_days: Optional[str] = None  # 품질유지기한일수
    usage: Optional[str] = None  # 용법
    purpose: Optional[str] = None  # 용도
    product_form: Optional[str] = None  # 제품형태
    packaging: Optional[str] = None  # 포장재질
    production_status: Optional[str] = None  # 생산종료여부
    high_calorie_food: Optional[str] = None  # 고열량저영양식품여부
    child_certified: Optional[str] = None  # 어린이기호식품품질인증여부
    last_update: Optional[str] = None  # 최종수정일자
    api_source: Optional[str] = None


class CompanyItem(BaseModel):
    """업체 정보 모델 (상세 정보 포함)"""
    company_name: str
    license_no: Optional[str] = None
    business_type: Optional[str] = None
    representative: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    license_date: Optional[str] = None
    # 상세 정보 (식품안전나라 I1220)
    phone: Optional[str] = None  # 전화번호
    institution: Optional[str] = None  # 기관명
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


class RepHistoryItem(BaseModel):
    """대표자 변경 이력 항목 모델"""
    representative: str
    change_date: Optional[str] = None
    change_type: Optional[str] = None
    license_no: Optional[str] = None


class RepHistoryResult(BaseModel):
    """대표자 변경 이력 결과 모델"""
    company_name: str
    total_count: int
    items: list[RepHistoryItem]


class LicenseChangeItem(BaseModel):
    """인허가 변경 이력 항목 모델"""
    company_name: str = ""
    business_type: str = ""
    license_no: str = ""
    phone: str = ""
    address: str = ""
    change_date: str = ""
    before_content: str = ""
    after_content: str = ""
    change_reason: str = ""


class LicenseChangeResult(BaseModel):
    """인허가 변경 이력 결과 모델"""
    company_name: str
    total_count: int
    items: list[LicenseChangeItem]


class FoodAPIService:
    """통합 식품 API 서비스 (공공데이터포털 + 식품안전나라)"""

    # 공공데이터포털 API
    DATA_GO_KR_APIS = {
        "food_product": {
            "name": "식품품목제조보고",
            "base_url": "http://apis.data.go.kr/1471000/FoodFlshdAddtvrptInfoService",
            "endpoint": "/getFoodFlshdAddtvrptInfoList",
        }
    }

    # 식품안전나라 API (폴백용)
    FOOD_SAFETY_APIS = {
        "I1220": {
            "name": "식품제조가공업정보",
            "service_id": "I1220",
            "description": "업체 정보 조회"
        },
        "I1250": {
            "name": "식품품목제조보고",
            "service_id": "I1250",
            "description": "품목 상세 정보 조회"
        },
        "I1300": {
            "name": "축산물가공업허가정보",
            "service_id": "I1300",
            "description": "축산 업체 정보 조회"
        },
        "I2859": {
            "name": "식품업소 인허가 변경 정보",
            "service_id": "I2859",
            "description": "식품 업소 인허가 변경 이력 조회"
        },
        "I2860": {
            "name": "건강기능식품업소 인허가 변경 정보",
            "service_id": "I2860",
            "description": "건강기능식품 업체 정보 조회"
        },
        "C002": {
            "name": "식품품목제조보고(원재료)",
            "service_id": "C002",
            "description": "품목 정보 + 원재료 조회"
        },
        "C003": {
            "name": "건강기능식품 품목제조신고(원재료)",
            "service_id": "C003",
            "description": "건강기능식품 품목 + 원재료 조회"
        },
        "C006": {
            "name": "건강기능식품 품목정보",
            "service_id": "C006",
            "description": "건강기능식품 품목 조회"
        }
    }

    FOOD_SAFETY_BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"

    def __init__(self):
        # 공공데이터포털 API 키 (이중 인코딩 방지를 위해 자동 디코딩)
        self.api_key_1 = self._decode_api_key(os.getenv("PUBLIC_DATA_API_KEY", ""))
        # 식품안전나라 API 키 (PUBLIC_DATA_API_KEY_2 또는 FOOD_SAFETY_API_KEY)
        self.food_safety_api_key = self._decode_api_key(
            os.getenv("PUBLIC_DATA_API_KEY_2", "") or os.getenv("FOOD_SAFETY_API_KEY", "")
        )
        # API 타임아웃 (초) - 빠른 폴백을 위해 짧게 설정
        self.api_timeout = 5.0

        # 디버그: API 키 로드 상태 출력
        print(f"[FoodAPIService 초기화]")
        print(f"  - api_key_1: {'설정됨 (' + self.api_key_1[:10] + '...)' if self.api_key_1 else '없음'}")
        print(f"  - food_safety_api_key: {'설정됨 (' + self.food_safety_api_key[:10] + '...)' if self.food_safety_api_key else '없음'}")

    def _decode_api_key(self, key: str) -> str:
        """URL 인코딩된 API 키를 자동 디코딩 (이중 인코딩 방지)"""
        if not key:
            return key
        # %가 포함되어 있으면 이미 인코딩된 키이므로 디코딩
        if "%" in key:
            return urllib.parse.unquote(key)
        return key

    async def search_companies(
        self,
        keyword: str = "",
        region: str = "",
        business_type: str = "",
        page: int = 1,
        per_page: int = 10
    ) -> CompanySearchResult:
        """업체 검색 (업종별 API 선택 + 폴백 구조)"""
        # 디버그: 수신된 파라미터 확인
        print(f"[업체검색] 수신 파라미터 - keyword: '{keyword}', region: '{region}', business_type: '{business_type}'")

        # 축산 업종인 경우 I1300 API 우선 사용
        if business_type == "축산" and self.food_safety_api_key:
            try:
                result = await self._search_livestock_companies(keyword, page, per_page)
                if result and result.total_count > 0:
                    filtered = self._filter_companies(result, region, business_type, keyword)
                    if filtered.total_count > 0:
                        return filtered
                    print(f"[축산 업체검색] 필터링 후 0건, 샘플 데이터로 폴백")
            except Exception as e:
                print(f"[축산 업체검색] I1300 오류: {e}")

        # 건강기능식품 업종인 경우 I2860 API 우선 사용
        if business_type == "건강기능식품" and self.food_safety_api_key:
            try:
                result = await self._search_health_food_companies(keyword, page, per_page)
                if result and result.total_count > 0:
                    filtered = self._filter_companies(result, region, business_type, keyword)
                    if filtered.total_count > 0:
                        return filtered
                    print(f"[건강기능식품 업체검색] 필터링 후 0건, 샘플 데이터로 폴백")
            except Exception as e:
                print(f"[건강기능식품 업체검색] 오류: {e}")

        # 1차: 식품안전나라 I1220 API (업체 검색 전용)
        if self.food_safety_api_key:
            try:
                result = await self._search_companies_food_safety(keyword, page, per_page)
                if result and result.total_count > 0:
                    filtered = self._filter_companies(result, region, business_type, keyword)
                    if filtered.total_count > 0:
                        return filtered
                    print(f"[업체검색] I1220 필터링 후 0건, 샘플 데이터로 폴백")
            except Exception as e:
                print(f"[업체검색] 식품안전나라 I1220 오류: {e}")

        # 3차: 샘플 데이터 반환
        return self._get_sample_companies(keyword, region, business_type, page, per_page)

    async def _search_companies_data_go_kr(
        self, keyword: str, page: int, per_page: int
    ) -> CompanySearchResult:
        """공공데이터포털 업체 검색"""
        async with httpx.AsyncClient(timeout=self.api_timeout) as client:
            params = {
                "serviceKey": self.api_key_1,
                "pageNo": str(page),
                "numOfRows": str(per_page * 5),
                "type": "json"
            }
            if keyword:
                params["BSSH_NM"] = keyword

            api_info = self.DATA_GO_KR_APIS["food_product"]
            url = f"{api_info['base_url']}{api_info['endpoint']}"
            print(f"[업체검색-공공데이터] 요청 URL: {url}")
            print(f"[업체검색-공공데이터] params: {params}")
            response = await client.get(url, params=params)
            print(f"[업체검색-공공데이터] 상태: {response.status_code}")
            print(f"[업체검색-공공데이터] 실제 URL: {response.url}")

            if response.status_code == 200:
                return self._parse_company_response(response.json(), page, per_page)
        return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_companies_food_safety(
        self, keyword: str, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I1220 업체 검색"""
        print(f"[I1220] 호출 시작 - keyword: '{keyword}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                start_idx = (page - 1) * per_page + 1
                end_idx = start_idx + per_page - 1

                # URL 형식: /api/키/I1220/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I1220/json/{start_idx}/{end_idx}"
                if keyword:
                    # URL 경로에 한글 직접 삽입 시 명시적 인코딩 필요
                    encoded_keyword = urllib.parse.quote(keyword, safe='')
                    url += f"/BSSH_NM={encoded_keyword}"

                print(f"[I1220] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[I1220] 응답 상태: {response.status_code}")
                print(f"[I1220] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_food_safety_company_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[I1220] 예외 발생: {type(e).__name__}: {e}")
            raise
        return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_health_food_companies(
        self, keyword: str, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I2860 건강기능식품 업체 검색"""
        print(f"[I2860] 건강기능식품 업체검색 시작 - keyword: '{keyword}'")
        async with httpx.AsyncClient(timeout=self.api_timeout) as client:
            # 키워드를 API에 전달하지 않고 더 많은 결과를 가져와서 로컬 필터링
            # (API가 정확히 일치하는 업체명만 반환하므로 부분 검색이 안 됨)
            url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I2860/json/1/500"

            print(f"[I2860] 요청 URL: {url}")
            response = await client.get(url)
            print(f"[I2860] 응답 상태: {response.status_code}")

            if response.status_code == 200:
                return self._parse_health_food_company_response(response.json(), page, per_page)
        return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_livestock_companies(
        self, keyword: str, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I1300 축산물 가공업 허가정보 검색"""
        print(f"[I1300] 축산물 업체검색 시작 - keyword: '{keyword}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                # 키워드를 API에 전달하지 않고 더 많은 결과를 가져와서 로컬 필터링
                # (API가 정확히 일치하는 업체명만 반환하므로 부분 검색이 안 됨)
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I1300/json/1/500"

                print(f"[I1300] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[I1300] 응답 상태: {response.status_code}")
                print(f"[I1300] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_livestock_company_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[I1300] 예외 발생: {type(e).__name__}: {e}")
            raise
        return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def search_products_by_company(
        self,
        company_name: str,
        page: int = 1,
        per_page: int = 20
    ) -> FoodSearchResult:
        """업체별 품목 검색 (C002/C003 원재료 포함 → I1250 폴백)"""

        # 1차: 식품안전나라 C002 API (식품 원재료 정보 포함)
        if self.food_safety_api_key:
            try:
                result = await self._search_products_c002(company_name, "", page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[품목검색] C002 오류: {e}")

        # 2차: 식품안전나라 C003 API (건강기능식품 원재료 정보 포함)
        if self.food_safety_api_key:
            try:
                result = await self._search_products_c003(company_name, "", page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[품목검색] C003 오류: {e}")

        # 3차: 식품안전나라 C006 API (건강기능식품 품목)
        if self.food_safety_api_key:
            try:
                result = await self._search_products_c006(company_name, "", page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[품목검색] C006 오류: {e}")

        # 4차: 식품안전나라 I1250 API 폴백
        if self.food_safety_api_key:
            try:
                result = await self._search_products_food_safety(company_name, "", page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[품목검색] I1250 오류: {e}")

        # 5차: 샘플 데이터 반환
        return self._get_sample_products_by_company(company_name, page, per_page)

    async def search_foods(
        self,
        keyword: str,
        page: int = 1,
        per_page: int = 10
    ) -> FoodSearchResult:
        """제품명으로 식품 검색 (공공데이터포털 → 식품안전나라 I1250 폴백)"""

        # 1차: 공공데이터포털 API 시도
        if self.api_key_1:
            try:
                result = await self._search_products_data_go_kr("", keyword, page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[식품검색] 공공데이터포털 오류: {e}")

        # 2차: 식품안전나라 I1250 API 폴백
        if self.food_safety_api_key:
            try:
                result = await self._search_products_food_safety("", keyword, page, per_page)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[식품검색] 식품안전나라 오류: {e}")

        # 3차: 샘플 데이터 반환
        return self._get_sample_foods(keyword, page, per_page)

    async def get_representative_history(
        self,
        company_name: str,
        license_no: str = ""
    ) -> RepHistoryResult:
        """대표자 변경 이력 조회 (I2860 건강기능식품 변경정보 API 활용)"""
        print(f"[대표자이력] 조회 시작 - company: '{company_name}', license: '{license_no}'")

        # 1차: I2860 건강기능식품 변경정보 API 시도 (인허가 변경정보 포함)
        if self.food_safety_api_key:
            try:
                result = await self._get_rep_history_i2860(company_name, license_no)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[대표자이력] I2860 오류: {e}")

        # 2차: 현재 대표자 정보만 반환 (I1220에서 조회)
        try:
            company_result = await self._search_companies_food_safety(company_name, 1, 1)
            if company_result and company_result.items:
                current_rep = company_result.items[0].representative
                if current_rep:
                    return RepHistoryResult(
                        company_name=company_name,
                        total_count=1,
                        items=[RepHistoryItem(
                            representative=current_rep,
                            change_date=company_result.items[0].license_date,
                            change_type="현재 대표자"
                        )]
                    )
        except Exception as e:
            print(f"[대표자이력] I1220 조회 오류: {e}")

        # 3차: 샘플 대표자 이력 반환
        return self._get_sample_rep_history(company_name)

    async def get_license_change_history(
        self,
        company_name: str,
        license_no: str = ""
    ) -> LicenseChangeResult:
        """인허가 변경 이력 조회 (I2859 식품업소 인허가 변경 정보 API)"""
        print(f"[인허가변경] 조회 시작 - company: '{company_name}', license: '{license_no}'")

        if self.food_safety_api_key:
            try:
                result = await self._get_license_change_i2859(company_name, license_no)
                if result and result.total_count > 0:
                    return result
            except Exception as e:
                print(f"[인허가변경] I2859 오류: {e}")

        # 빈 결과 반환
        return LicenseChangeResult(company_name=company_name, total_count=0, items=[])

    async def _get_license_change_i2859(
        self, company_name: str, license_no: str
    ) -> LicenseChangeResult:
        """식품안전나라 I2859 식품업소 인허가 변경 정보 조회"""
        print(f"[I2859] 호출 - company: '{company_name}', license: '{license_no}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                # URL 형식: /api/키/I2859/json/시작/끝/BSSH_NM=값&LCNS_NO=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I2859/json/1/100"

                # 검색 조건 추가
                params = []
                if license_no:
                    encoded_license = urllib.parse.quote(license_no, safe='')
                    params.append(f"LCNS_NO={encoded_license}")
                if company_name:
                    encoded_company = urllib.parse.quote(company_name, safe='')
                    params.append(f"BSSH_NM={encoded_company}")

                if params:
                    url += "/" + "&".join(params)

                print(f"[I2859] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[I2859] 응답 상태: {response.status_code}")
                print(f"[I2859] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_license_change_i2859(response.json(), company_name)
        except Exception as e:
            print(f"[I2859] 예외: {type(e).__name__}: {e}")
            raise
        return LicenseChangeResult(company_name=company_name, total_count=0, items=[])

    def _parse_license_change_i2859(
        self, data: dict, company_name: str
    ) -> LicenseChangeResult:
        """I2859 인허가 변경 이력 응답 파싱"""
        try:
            service_data = data.get("I2859", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return LicenseChangeResult(company_name=company_name, total_count=0, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                change_item = LicenseChangeItem(
                    company_name=item.get("BSSH_NM", ""),
                    business_type=item.get("INDUTY_CD_NM", ""),
                    license_no=item.get("LCNS_NO", ""),
                    phone=item.get("TELNO", ""),
                    address=item.get("SITE_ADDR", ""),
                    change_date=item.get("CHNG_DT", ""),
                    before_content=item.get("CHNG_BF_CN", ""),
                    after_content=item.get("CHNG_AF_CN", ""),
                    change_reason=item.get("CHNG_PRVNS", "")
                )
                items.append(change_item)

            # 변경일 기준 정렬 (최신순)
            items.sort(key=lambda x: x.change_date or "", reverse=True)

            return LicenseChangeResult(
                company_name=company_name,
                total_count=total_count,
                items=items
            )
        except Exception as e:
            print(f"[I2859] 파싱 오류: {e}")
            return LicenseChangeResult(company_name=company_name, total_count=0, items=[])

    async def _get_rep_history_i2860(
        self, company_name: str, license_no: str
    ) -> RepHistoryResult:
        """식품안전나라 I2860 건강기능식품 인허가 변경 이력 조회"""
        print(f"[I2860 이력] 호출 - company: '{company_name}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                # URL 형식: /api/키/I2860/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I2860/json/1/100"
                if company_name:
                    encoded_keyword = urllib.parse.quote(company_name, safe='')
                    url += f"/BSSH_NM={encoded_keyword}"

                print(f"[I2860 이력] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[I2860 이력] 응답 상태: {response.status_code}")

                if response.status_code == 200:
                    return self._parse_rep_history_i2860(response.json(), company_name)
        except Exception as e:
            print(f"[I2860 이력] 예외: {type(e).__name__}: {e}")
            raise
        return RepHistoryResult(company_name=company_name, total_count=0, items=[])

    def _parse_rep_history_i2860(
        self, data: dict, company_name: str
    ) -> RepHistoryResult:
        """I2860 대표자 변경 이력 응답 파싱"""
        try:
            service_data = data.get("I2860", {})
            items_data = service_data.get("row", [])

            if not items_data:
                return RepHistoryResult(company_name=company_name, total_count=0, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            # 변경이력에서 대표자 관련 항목 추출
            history_items = []
            seen_reps = set()

            for item in items_data:
                # 변경사유에 대표자 관련 내용이 있는지 확인
                change_reason = item.get("CHNG_RESON_CN", "")
                change_date = item.get("CHNG_DT", "") or item.get("CHNG_APVL_DT", "")
                change_type = item.get("CHNG_CN", "")

                # 대표자명 추출 (PRSDNT_NM 또는 변경사유에서)
                rep_name = item.get("PRSDNT_NM", "")
                if not rep_name:
                    # 변경사유에서 대표자명 추출 시도
                    if "대표" in change_reason:
                        rep_name = change_reason

                if rep_name and rep_name not in seen_reps:
                    seen_reps.add(rep_name)
                    history_items.append(RepHistoryItem(
                        representative=rep_name,
                        change_date=change_date,
                        change_type=change_type or "변경",
                        license_no=item.get("LCNS_NO", "")
                    ))

            # 변경일 기준 정렬 (최신순)
            history_items.sort(key=lambda x: x.change_date or "", reverse=True)

            return RepHistoryResult(
                company_name=company_name,
                total_count=len(history_items),
                items=history_items
            )
        except Exception as e:
            print(f"[I2860 이력] 파싱 오류: {e}")
            return RepHistoryResult(company_name=company_name, total_count=0, items=[])

    def _get_sample_rep_history(self, company_name: str) -> RepHistoryResult:
        """샘플 대표자 변경 이력"""
        # 샘플 대표자 변경 이력 데이터
        sample_history = {
            "삼양식품(주)": [
                RepHistoryItem(representative="김정수", change_date="2020-03-15", change_type="현재 대표자"),
                RepHistoryItem(representative="김윤", change_date="2015-01-20", change_type="대표자 변경"),
                RepHistoryItem(representative="전중윤", change_date="2008-05-10", change_type="대표자 변경"),
            ],
            "농심(주)": [
                RepHistoryItem(representative="이병학", change_date="2021-12-01", change_type="현재 대표자"),
                RepHistoryItem(representative="박준", change_date="2017-03-15", change_type="대표자 변경"),
                RepHistoryItem(representative="신춘호", change_date="2003-07-01", change_type="대표자 변경"),
            ],
            "CJ제일제당(주)": [
                RepHistoryItem(representative="최은석", change_date="2022-04-01", change_type="현재 대표자"),
                RepHistoryItem(representative="강신호", change_date="2018-09-01", change_type="대표자 변경"),
            ],
            "오뚜기(주)": [
                RepHistoryItem(representative="함영준", change_date="2019-06-01", change_type="현재 대표자"),
                RepHistoryItem(representative="함태호", change_date="1980-01-01", change_type="설립"),
            ],
            "롯데제과(주)": [
                RepHistoryItem(representative="민명기", change_date="2021-09-01", change_type="현재 대표자"),
                RepHistoryItem(representative="이재혁", change_date="2017-11-01", change_type="대표자 변경"),
            ],
            "하림(주)": [
                RepHistoryItem(representative="김홍국", change_date="2000-01-01", change_type="현재 대표자"),
            ],
            "빙그레(주)": [
                RepHistoryItem(representative="전창원", change_date="2019-03-01", change_type="현재 대표자"),
                RepHistoryItem(representative="박영호", change_date="2010-05-01", change_type="대표자 변경"),
            ],
        }

        items = sample_history.get(company_name, [])
        return RepHistoryResult(
            company_name=company_name,
            total_count=len(items),
            items=items
        )

    async def _search_products_data_go_kr(
        self, company_name: str, product_name: str, page: int, per_page: int
    ) -> FoodSearchResult:
        """공공데이터포털 품목 검색"""
        async with httpx.AsyncClient(timeout=self.api_timeout) as client:
            params = {
                "serviceKey": self.api_key_1,
                "pageNo": str(page),
                "numOfRows": str(per_page),
                "type": "json"
            }
            if company_name:
                params["BSSH_NM"] = company_name
            if product_name:
                params["PRDLST_NM"] = product_name

            api_info = self.DATA_GO_KR_APIS["food_product"]
            url = f"{api_info['base_url']}{api_info['endpoint']}"
            response = await client.get(url, params=params)
            print(f"[품목검색-공공데이터] 상태: {response.status_code}")

            if response.status_code == 200:
                return self._parse_food_product_response(response.json(), page, per_page)
        return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_products_food_safety(
        self, company_name: str, product_name: str, page: int, per_page: int
    ) -> FoodSearchResult:
        """식품안전나라 I1250 품목 검색 (상세 정보 포함)"""
        print(f"[I1250] 호출 시작 - company: '{company_name}', product: '{product_name}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                start_idx = (page - 1) * per_page + 1
                end_idx = start_idx + per_page - 1

                # URL 형식: /api/키/I1250/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/I1250/json/{start_idx}/{end_idx}"

                # 검색 조건 추가 (한글 URL 인코딩 필수)
                if company_name:
                    encoded_company = urllib.parse.quote(company_name, safe='')
                    url += f"/BSSH_NM={encoded_company}"
                if product_name:
                    encoded_product = urllib.parse.quote(product_name, safe='')
                    url += f"/PRDLST_NM={encoded_product}"

                print(f"[I1250] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[I1250] 응답 상태: {response.status_code}")
                print(f"[I1250] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_food_safety_product_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[I1250] 예외 발생: {type(e).__name__}: {e}")
            raise
        return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_products_c002(
        self, company_name: str, product_name: str, page: int, per_page: int
    ) -> FoodSearchResult:
        """식품안전나라 C002 품목 검색 (원재료 정보 포함)"""
        print(f"[C002] 호출 시작 - company: '{company_name}', product: '{product_name}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                start_idx = (page - 1) * per_page + 1
                end_idx = start_idx + per_page - 1

                # URL 형식: /api/키/C002/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/C002/json/{start_idx}/{end_idx}"

                # 검색 조건 추가 (한글 URL 인코딩 필수)
                if company_name:
                    encoded_company = urllib.parse.quote(company_name, safe='')
                    url += f"/BSSH_NM={encoded_company}"
                if product_name:
                    encoded_product = urllib.parse.quote(product_name, safe='')
                    url += f"/PRDLST_NM={encoded_product}"

                print(f"[C002] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[C002] 응답 상태: {response.status_code}")
                print(f"[C002] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_c002_product_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[C002] 예외 발생: {type(e).__name__}: {e}")
            raise
        return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_c002_product_response(
        self, data: dict, page: int, per_page: int
    ) -> FoodSearchResult:
        """C002 API 응답 파싱 (원재료 정보 포함)"""
        try:
            service_data = data.get("C002", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDLST_DCNM", ""),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    raw_materials=item.get("RAWMTRL_NM", ""),  # 원재료 정보!
                    license_no=item.get("LCNS_NO", ""),
                    permit_date=item.get("PRMS_DT", ""),
                    last_update=item.get("CHNG_DT", ""),
                    api_source="식품안전나라(C002)"
                )
                items.append(food)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[C002] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_products_c003(
        self, company_name: str, product_name: str, page: int, per_page: int
    ) -> FoodSearchResult:
        """식품안전나라 C003 건강기능식품 품목제조신고(원재료) 검색"""
        print(f"[C003] 호출 시작 - company: '{company_name}', product: '{product_name}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                start_idx = (page - 1) * per_page + 1
                end_idx = start_idx + per_page - 1

                # URL 형식: /api/키/C003/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/C003/json/{start_idx}/{end_idx}"

                # 검색 조건 추가 (한글 URL 인코딩 필수)
                if company_name:
                    encoded_company = urllib.parse.quote(company_name, safe='')
                    url += f"/BSSH_NM={encoded_company}"
                if product_name:
                    encoded_product = urllib.parse.quote(product_name, safe='')
                    url += f"/PRDLST_NM={encoded_product}"

                print(f"[C003] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[C003] 응답 상태: {response.status_code}")
                print(f"[C003] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_c003_product_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[C003] 예외 발생: {type(e).__name__}: {e}")
            raise
        return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_c003_product_response(
        self, data: dict, page: int, per_page: int
    ) -> FoodSearchResult:
        """C003 API 응답 파싱 (건강기능식품 원재료 정보 포함)"""
        try:
            service_data = data.get("C003", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDLST_DCNM", "건강기능식품"),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    raw_materials=item.get("RAWMTRL_NM", ""),  # 원재료 정보
                    license_no=item.get("LCNS_NO", ""),
                    permit_date=item.get("PRMS_DT", ""),
                    last_update=item.get("CHNG_DT", ""),
                    api_source="식품안전나라(C003)"
                )
                items.append(food)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[C003] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    async def _search_products_c006(
        self, company_name: str, product_name: str, page: int, per_page: int
    ) -> FoodSearchResult:
        """식품안전나라 C006 건강기능식품 품목정보 검색"""
        print(f"[C006] 호출 시작 - company: '{company_name}', product: '{product_name}'")
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                start_idx = (page - 1) * per_page + 1
                end_idx = start_idx + per_page - 1

                # URL 형식: /api/키/C006/json/시작/끝/BSSH_NM=값
                url = f"{self.FOOD_SAFETY_BASE_URL}/{self.food_safety_api_key}/C006/json/{start_idx}/{end_idx}"

                # 검색 조건 추가 (한글 URL 인코딩 필수)
                if company_name:
                    encoded_company = urllib.parse.quote(company_name, safe='')
                    url += f"/BSSH_NM={encoded_company}"
                if product_name:
                    encoded_product = urllib.parse.quote(product_name, safe='')
                    url += f"/PRDLST_NM={encoded_product}"

                print(f"[C006] 요청 URL: {url}")
                response = await client.get(url)
                print(f"[C006] 응답 상태: {response.status_code}")
                print(f"[C006] 응답 본문 (처음 500자): {response.text[:500]}")

                if response.status_code == 200:
                    return self._parse_c006_product_response(response.json(), page, per_page)
        except Exception as e:
            print(f"[C006] 예외 발생: {type(e).__name__}: {e}")
            raise
        return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_c006_product_response(
        self, data: dict, page: int, per_page: int
    ) -> FoodSearchResult:
        """C006 API 응답 파싱 (건강기능식품 품목정보)"""
        try:
            service_data = data.get("C006", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDLST_DCNM", "건강기능식품"),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    license_no=item.get("LCNS_NO", ""),
                    permit_date=item.get("PRMS_DT", ""),
                    last_update=item.get("CHNG_DT", ""),
                    api_source="식품안전나라(C006)"
                )
                items.append(food)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[C006] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _filter_companies(
        self,
        result: CompanySearchResult,
        region: str,
        business_type: str,
        keyword: str = ""
    ) -> CompanySearchResult:
        """업체 결과 필터링 (키워드, 지역, 업종)"""
        items = result.items

        # 키워드 필터 (업체명에 키워드 포함 여부)
        if keyword:
            keyword_lower = keyword.lower()
            items = [
                c for c in items
                if keyword_lower in (c.company_name or "").lower()
            ]

        # 지역 필터 (콤마로 구분된 여러 지역)
        if region:
            regions = [r.strip() for r in region.split(',') if r.strip()]
            if regions:
                items = [
                    c for c in items
                    if any(r in (c.address or "") or r in (c.region or "") for r in regions)
                ]

        # 업종 필터
        if business_type:
            items = [
                c for c in items
                if business_type.lower() in (c.business_type or "").lower()
            ]

        return CompanySearchResult(
            total_count=len(items),
            page=result.page,
            per_page=result.per_page,
            items=items
        )

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
                        api_source="공공데이터"
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
                    api_source="공공데이터"
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

    def _safe_float(self, value) -> Optional[float]:
        """안전한 float 변환"""
        if value is None or value == "":
            return None
        try:
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _parse_food_safety_company_response(
        self, data: dict, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I1220 업체 응답 파싱 (상세 정보 포함)"""
        try:
            # 식품안전나라 응답 구조: {서비스명: {row: [...], total_count: ...}}
            service_data = data.get("I1220", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                company = CompanyItem(
                    company_name=item.get("BSSH_NM", ""),
                    license_no=item.get("LCNS_NO", ""),
                    business_type=item.get("INDUTY_NM", ""),
                    representative=item.get("PRSDNT_NM", ""),
                    address=item.get("LOCP_ADDR", ""),
                    license_date=item.get("PRMS_DT", ""),
                    phone=item.get("TELNO", ""),
                    institution=item.get("INSTT_NM", ""),
                    status="운영",
                    api_source="식품안전나라"
                )
                items.append(company)

            return CompanySearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[식품안전나라-업체] 파싱 오류: {e}")
            return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_health_food_company_response(
        self, data: dict, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I2860 건강기능식품 업체 응답 파싱"""
        try:
            # 식품안전나라 응답 구조: {서비스명: {row: [...], total_count: ...}}
            service_data = data.get("I2860", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            # 업체명으로 중복 제거
            companies_dict = {}
            for item in items_data:
                company_name = item.get("BSSH_NM", "")
                if company_name and company_name not in companies_dict:
                    companies_dict[company_name] = CompanyItem(
                        company_name=company_name,
                        license_no=item.get("LCNS_NO", ""),
                        business_type=item.get("INDUTY_CD_NM", "건강기능식품"),
                        address=item.get("SITE_ADDR", ""),
                        phone=item.get("TELNO", ""),
                        status="운영",
                        api_source="식품안전나라"
                    )

            items = list(companies_dict.values())

            return CompanySearchResult(
                total_count=len(items),
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[건강기능식품-업체] 파싱 오류: {e}")
            return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_livestock_company_response(
        self, data: dict, page: int, per_page: int
    ) -> CompanySearchResult:
        """식품안전나라 I1300 축산물 가공업 허가정보 응답 파싱"""
        try:
            # 식품안전나라 응답 구조: {서비스명: {row: [...], total_count: ...}}
            service_data = data.get("I1300", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            # 업체명으로 중복 제거
            companies_dict = {}
            for item in items_data:
                company_name = item.get("BSSH_NM", "")
                if company_name and company_name not in companies_dict:
                    companies_dict[company_name] = CompanyItem(
                        company_name=company_name,
                        license_no=item.get("LCNS_NO", ""),
                        business_type="축산",
                        representative=item.get("PRSDNT_NM", ""),
                        address=item.get("SITE_ADDR", "") or item.get("LOCP_ADDR", ""),
                        phone=item.get("TELNO", ""),
                        license_date=item.get("PRMS_DT", ""),
                        status="운영",
                        api_source="식품안전나라(I1300)"
                    )

            items = list(companies_dict.values())

            return CompanySearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[축산-업체] 파싱 오류: {e}")
            return CompanySearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _parse_food_safety_product_response(
        self, data: dict, page: int, per_page: int
    ) -> FoodSearchResult:
        """식품안전나라 I1250 품목 응답 파싱 (상세 정보 포함)"""
        try:
            # 식품안전나라 응답 구조: {서비스명: {row: [...], total_count: ...}}
            service_data = data.get("I1250", {})
            total_count = int(service_data.get("total_count", "0"))
            items_data = service_data.get("row", [])

            if not items_data:
                return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

            if isinstance(items_data, dict):
                items_data = [items_data]

            items = []
            for item in items_data:
                food = FoodItem(
                    food_name=item.get("PRDLST_NM", ""),
                    food_code=item.get("PRDLST_REPORT_NO", ""),
                    category=item.get("PRDLST_DCNM", ""),
                    manufacturer=item.get("BSSH_NM", ""),
                    report_no=item.get("PRDLST_REPORT_NO", ""),
                    # 상세 정보
                    license_no=item.get("LCNS_NO", ""),
                    permit_date=item.get("PRMS_DT", ""),
                    expiry_date=item.get("POG_DAYCNT", ""),
                    shelf_life_days=item.get("QLITY_MNTNC_TMLMT_DAYCNT", ""),
                    usage=item.get("USAGE", ""),
                    purpose=item.get("PRPOS", ""),
                    product_form=item.get("DISPOS", ""),
                    packaging=item.get("FRMLC_MTRQLT", ""),
                    production_status=item.get("PRODUCTION", ""),
                    high_calorie_food=item.get("HIENG_LNTRT_DVS_NM", ""),
                    child_certified=item.get("CHILD_CRTFC_YN", ""),
                    last_update=item.get("LAST_UPDT_DTM", ""),
                    api_source="식품안전나라"
                )
                items.append(food)

            return FoodSearchResult(
                total_count=total_count,
                page=page,
                per_page=per_page,
                items=items
            )
        except Exception as e:
            print(f"[식품안전나라-품목] 파싱 오류: {e}")
            return FoodSearchResult(total_count=0, page=page, per_page=per_page, items=[])

    def _get_sample_companies(
        self,
        keyword: str,
        region: str,
        business_type: str,
        page: int,
        per_page: int
    ) -> CompanySearchResult:
        """샘플 업체 데이터 (확장)"""
        sample_companies = [
            # 서울
            CompanyItem(company_name="삼양식품(주)", license_no="19670001", business_type="식품",
                       representative="김정수", address="서울특별시 성북구 삼양로 123", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="농심(주)", license_no="19680002", business_type="식품",
                       representative="이병학", address="서울특별시 동작구 신대방동 456", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="CJ제일제당(주)", license_no="19530004", business_type="식품",
                       representative="최은석", address="서울특별시 중구 을지로 123", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="대상(주)", license_no="19560005", business_type="식품",
                       representative="임정배", address="서울특별시 종로구 종로 456", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="풀무원식품(주)", license_no="19840006", business_type="식품",
                       representative="이효율", address="서울특별시 강남구 테헤란로 789", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="롯데제과(주)", license_no="19670008", business_type="식품",
                       representative="민명기", address="서울특별시 영등포구 양평동 111", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="해태제과(주)", license_no="19680010", business_type="식품",
                       representative="신정훈", address="서울특별시 용산구 한강로 222", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="동서식품(주)", license_no="19680011", business_type="식품",
                       representative="김광수", address="서울특별시 강남구 삼성동 333", region="서울", status="운영", api_source="샘플"),
            # 경기
            CompanyItem(company_name="오뚜기(주)", license_no="19690003", business_type="식품",
                       representative="함영준", address="경기도 안양시 동안구 평촌동 123", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="빙그레(주)", license_no="19670007", business_type="식품",
                       representative="전창원", address="경기도 남양주시 진접읍 456", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="매일유업(주)", license_no="19690012", business_type="식품",
                       representative="김선희", address="경기도 용인시 기흥구 789", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="남양유업(주)", license_no="19640013", business_type="식품",
                       representative="이광범", address="경기도 세종시 세종로 111", region="경기", status="운영", api_source="샘플"),
            # 축산
            CompanyItem(company_name="하림(주)", license_no="19860014", business_type="축산",
                       representative="김홍국", address="전북특별자치도 익산시 왕궁면 789", region="전북", status="운영", api_source="샘플"),
            CompanyItem(company_name="마니커(주)", license_no="19920201", business_type="축산",
                       representative="박철", address="충청남도 천안시 동남구 123", region="충남", status="운영", api_source="샘플"),
            CompanyItem(company_name="선진(주)", license_no="19800202", business_type="축산",
                       representative="이범권", address="경기도 파주시 문산읍 456", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="목우촌(주)", license_no="19840203", business_type="축산",
                       representative="이상열", address="경상북도 영천시 북안면 789", region="경북", status="운영", api_source="샘플"),
            CompanyItem(company_name="도드람푸드(주)", license_no="19950204", business_type="축산",
                       representative="박광욱", address="경기도 안성시 미양면 111", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="체리부로(주)", license_no="19850205", business_type="축산",
                       representative="정희용", address="충청북도 음성군 대소면 222", region="충북", status="운영", api_source="샘플"),
            CompanyItem(company_name="사조팜스(주)", license_no="19900206", business_type="축산",
                       representative="주지홍", address="경상북도 상주시 함창읍 333", region="경북", status="운영", api_source="샘플"),
            # 부산
            CompanyItem(company_name="삼진어묵(주)", license_no="19530020", business_type="식품",
                       representative="박용준", address="부산광역시 영도구 봉래동 123", region="부산", status="운영", api_source="샘플"),
            CompanyItem(company_name="동원F&B(주) 부산공장", license_no="19690021", business_type="식품",
                       representative="김재철", address="부산광역시 사하구 장림동 456", region="부산", status="운영", api_source="샘플"),
            # 대구
            CompanyItem(company_name="팔도(주)", license_no="19830030", business_type="식품",
                       representative="이영재", address="대구광역시 달성군 다사읍 123", region="대구", status="운영", api_source="샘플"),
            # 충북
            CompanyItem(company_name="청정원(주)", license_no="19870040", business_type="식품",
                       representative="임정배", address="충청북도 청주시 흥덕구 123", region="충북", status="운영", api_source="샘플"),
            # 충남
            CompanyItem(company_name="사조대림(주)", license_no="19710041", business_type="식품",
                       representative="주지홍", address="충청남도 아산시 배방읍 456", region="충남", status="운영", api_source="샘플"),
            # 전북
            CompanyItem(company_name="동원F&B(주)", license_no="19690050", business_type="식품",
                       representative="김재철", address="전북특별자치도 익산시 왕궁면 789", region="전북", status="운영", api_source="샘플"),
            # 경북
            CompanyItem(company_name="정식품(주)", license_no="19730060", business_type="식품",
                       representative="박승주", address="경상북도 칠곡군 지천면 123", region="경북", status="운영", api_source="샘플"),
            # 경남
            CompanyItem(company_name="사조해표(주)", license_no="19720070", business_type="식품",
                       representative="주지홍", address="경상남도 창원시 마산회원구 456", region="경남", status="운영", api_source="샘플"),
            # 건강기능식품
            CompanyItem(company_name="한국야쿠르트(주)", license_no="19710100", business_type="건강기능식품",
                       representative="김병진", address="서울특별시 서초구 서초동 123", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="종근당건강(주)", license_no="19830101", business_type="건강기능식품",
                       representative="김영주", address="서울특별시 강동구 성내동 456", region="서울", status="운영", api_source="샘플"),
            CompanyItem(company_name="뉴트리(주)", license_no="20000102", business_type="건강기능식품",
                       representative="강준희", address="경기도 성남시 분당구 789", region="경기", status="운영", api_source="샘플"),
            CompanyItem(company_name="고려은단(주)", license_no="19730103", business_type="건강기능식품",
                       representative="장영호", address="서울특별시 강남구 역삼동 111", region="서울", status="운영", api_source="샘플"),
        ]

        # 필터링
        filtered = sample_companies

        # 키워드 필터
        if keyword:
            filtered = [c for c in filtered if keyword.lower() in c.company_name.lower()]

        # 지역 필터 (콤마로 구분된 여러 지역)
        if region:
            regions = [r.strip() for r in region.split(',') if r.strip()]
            if regions:
                filtered = [
                    c for c in filtered
                    if any(r in (c.address or "") or r in (c.region or "") for r in regions)
                ]

        # 업종 필터
        if business_type:
            filtered = [
                c for c in filtered
                if business_type.lower() in (c.business_type or "").lower()
            ]

        # 페이지네이션
        total = len(filtered)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]

        return CompanySearchResult(
            total_count=total,
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
        """샘플 업체별 품목 데이터 (확장)"""
        sample_products = {
            "농심(주)": [
                FoodItem(food_name="신라면", category="라면", manufacturer="농심(주)", report_no="NM001", raw_materials="밀가루, 팜유, 전분, 고춧가루", api_source="샘플"),
                FoodItem(food_name="안성탕면", category="라면", manufacturer="농심(주)", report_no="NM002", raw_materials="밀가루, 팜유, 된장분말", api_source="샘플"),
                FoodItem(food_name="짜파게티", category="라면", manufacturer="농심(주)", report_no="NM003", raw_materials="밀가루, 팜유, 춘장분말", api_source="샘플"),
                FoodItem(food_name="너구리", category="라면", manufacturer="농심(주)", report_no="NM004", raw_materials="밀가루, 팜유, 다시마", api_source="샘플"),
                FoodItem(food_name="새우깡", category="스낵", manufacturer="농심(주)", report_no="NM005", raw_materials="밀가루, 새우분말, 팜유", api_source="샘플"),
                FoodItem(food_name="양파링", category="스낵", manufacturer="농심(주)", report_no="NM006", raw_materials="밀가루, 양파분말, 팜유", api_source="샘플"),
                FoodItem(food_name="포테토칩 오리지널", category="스낵", manufacturer="농심(주)", report_no="NM007", raw_materials="감자, 팜유, 소금", api_source="샘플"),
            ],
            "삼양식품(주)": [
                FoodItem(food_name="삼양라면", category="라면", manufacturer="삼양식품(주)", report_no="SY001", raw_materials="밀가루, 팜유, 소금", api_source="샘플"),
                FoodItem(food_name="불닭볶음면", category="라면", manufacturer="삼양식품(주)", report_no="SY002", raw_materials="밀가루, 팜유, 고춧가루, 캡사이신", api_source="샘플"),
                FoodItem(food_name="짜짜로니", category="라면", manufacturer="삼양식품(주)", report_no="SY003", raw_materials="밀가루, 팜유, 춘장", api_source="샘플"),
                FoodItem(food_name="까르보불닭볶음면", category="라면", manufacturer="삼양식품(주)", report_no="SY004", raw_materials="밀가루, 팜유, 크림분말", api_source="샘플"),
                FoodItem(food_name="핵불닭볶음면", category="라면", manufacturer="삼양식품(주)", report_no="SY005", raw_materials="밀가루, 팜유, 청양고추", api_source="샘플"),
            ],
            "오뚜기(주)": [
                FoodItem(food_name="진라면 순한맛", category="라면", manufacturer="오뚜기(주)", report_no="OT001", raw_materials="밀가루, 팜유, 소고기분말", api_source="샘플"),
                FoodItem(food_name="진라면 매운맛", category="라면", manufacturer="오뚜기(주)", report_no="OT002", raw_materials="밀가루, 팜유, 고춧가루", api_source="샘플"),
                FoodItem(food_name="참깨라면", category="라면", manufacturer="오뚜기(주)", report_no="OT003", raw_materials="밀가루, 팜유, 참깨", api_source="샘플"),
                FoodItem(food_name="오뚜기 카레 순한맛", category="즉석조리", manufacturer="오뚜기(주)", report_no="OT004", raw_materials="카레분말, 양파, 감자", api_source="샘플"),
                FoodItem(food_name="3분 짜장", category="즉석조리", manufacturer="오뚜기(주)", report_no="OT005", raw_materials="춘장, 돼지고기, 양파", api_source="샘플"),
                FoodItem(food_name="케찹", category="소스", manufacturer="오뚜기(주)", report_no="OT006", raw_materials="토마토, 설탕, 식초", api_source="샘플"),
            ],
            "CJ제일제당(주)": [
                FoodItem(food_name="햇반", category="즉석밥", manufacturer="CJ제일제당(주)", report_no="CJ001", raw_materials="쌀, 정제수", api_source="샘플"),
                FoodItem(food_name="비비고 왕교자", category="만두", manufacturer="CJ제일제당(주)", report_no="CJ002", raw_materials="밀가루, 돼지고기, 배추", api_source="샘플"),
                FoodItem(food_name="스팸 클래식", category="캔햄", manufacturer="CJ제일제당(주)", report_no="CJ003", raw_materials="돼지고기, 전분, 소금", api_source="샘플"),
                FoodItem(food_name="다시다", category="조미료", manufacturer="CJ제일제당(주)", report_no="CJ004", raw_materials="소고기엑기스, 소금, MSG", api_source="샘플"),
                FoodItem(food_name="백설 식용유", category="식용유", manufacturer="CJ제일제당(주)", report_no="CJ005", raw_materials="대두유", api_source="샘플"),
            ],
            "롯데제과(주)": [
                FoodItem(food_name="초코파이", category="과자", manufacturer="롯데제과(주)", report_no="LT001", raw_materials="밀가루, 설탕, 초콜릿", api_source="샘플"),
                FoodItem(food_name="빼빼로", category="과자", manufacturer="롯데제과(주)", report_no="LT002", raw_materials="밀가루, 초콜릿, 설탕", api_source="샘플"),
                FoodItem(food_name="꼬깔콘", category="스낵", manufacturer="롯데제과(주)", report_no="LT003", raw_materials="옥수수, 팜유, 소금", api_source="샘플"),
                FoodItem(food_name="칸쵸", category="과자", manufacturer="롯데제과(주)", report_no="LT004", raw_materials="밀가루, 설탕, 초콜릿", api_source="샘플"),
            ],
            "빙그레(주)": [
                FoodItem(food_name="바나나맛우유", category="가공유", manufacturer="빙그레(주)", report_no="BG001", raw_materials="원유, 설탕, 바나나농축액", api_source="샘플"),
                FoodItem(food_name="메로나", category="아이스크림", manufacturer="빙그레(주)", report_no="BG002", raw_materials="정제수, 설탕, 멜론농축액", api_source="샘플"),
                FoodItem(food_name="투게더", category="아이스크림", manufacturer="빙그레(주)", report_no="BG003", raw_materials="원유, 설탕, 바닐라향", api_source="샘플"),
                FoodItem(food_name="요플레", category="발효유", manufacturer="빙그레(주)", report_no="BG004", raw_materials="원유, 유산균, 설탕", api_source="샘플"),
            ],
            "풀무원식품(주)": [
                FoodItem(food_name="풀무원 두부", category="두부", manufacturer="풀무원식품(주)", report_no="PM001", raw_materials="대두, 정제수, 응고제", api_source="샘플"),
                FoodItem(food_name="생면식감 라면", category="라면", manufacturer="풀무원식품(주)", report_no="PM002", raw_materials="밀가루, 팜유, 소금", api_source="샘플"),
                FoodItem(food_name="김치", category="김치", manufacturer="풀무원식품(주)", report_no="PM003", raw_materials="배추, 고춧가루, 젓갈", api_source="샘플"),
            ],
            "대상(주)": [
                FoodItem(food_name="청정원 순창고추장", category="장류", manufacturer="대상(주)", report_no="DS001", raw_materials="고춧가루, 찹쌀, 메주", api_source="샘플"),
                FoodItem(food_name="청정원 된장", category="장류", manufacturer="대상(주)", report_no="DS002", raw_materials="대두, 소금, 밀", api_source="샘플"),
                FoodItem(food_name="미원", category="조미료", manufacturer="대상(주)", report_no="DS003", raw_materials="MSG", api_source="샘플"),
            ],
            "한국야쿠르트(주)": [
                FoodItem(food_name="야쿠르트", category="발효유", manufacturer="한국야쿠르트(주)", report_no="YK001", raw_materials="탈지분유, 유산균, 설탕", api_source="샘플"),
                FoodItem(food_name="쿠퍼스", category="건강음료", manufacturer="한국야쿠르트(주)", report_no="YK002", raw_materials="정제수, 비타민, 미네랄", api_source="샘플"),
            ],
            # 축산 업체
            "하림(주)": [
                FoodItem(food_name="하림 IFF 치킨너겟", category="닭고기가공품", manufacturer="하림(주)", report_no="HR001", raw_materials="닭고기, 밀가루, 빵가루", api_source="샘플"),
                FoodItem(food_name="하림 닭가슴살", category="닭고기", manufacturer="하림(주)", report_no="HR002", raw_materials="닭가슴살", api_source="샘플"),
                FoodItem(food_name="하림 치킨까스", category="닭고기가공품", manufacturer="하림(주)", report_no="HR003", raw_materials="닭고기, 밀가루, 빵가루", api_source="샘플"),
                FoodItem(food_name="하림 닭볶음탕용", category="닭고기", manufacturer="하림(주)", report_no="HR004", raw_materials="닭고기", api_source="샘플"),
                FoodItem(food_name="하림 더미니 소시지", category="소시지", manufacturer="하림(주)", report_no="HR005", raw_materials="닭고기, 전분, 소금", api_source="샘플"),
            ],
            "마니커(주)": [
                FoodItem(food_name="마니커 순살치킨", category="닭고기가공품", manufacturer="마니커(주)", report_no="MK001", raw_materials="닭고기, 밀가루, 전분", api_source="샘플"),
                FoodItem(food_name="마니커 치킨텐더", category="닭고기가공품", manufacturer="마니커(주)", report_no="MK002", raw_materials="닭고기, 밀가루, 빵가루", api_source="샘플"),
                FoodItem(food_name="마니커 닭다리살", category="닭고기", manufacturer="마니커(주)", report_no="MK003", raw_materials="닭다리살", api_source="샘플"),
            ],
            "선진(주)": [
                FoodItem(food_name="선진 한돈 삼겹살", category="돼지고기", manufacturer="선진(주)", report_no="SJ001", raw_materials="돼지고기", api_source="샘플"),
                FoodItem(food_name="선진 한돈 목살", category="돼지고기", manufacturer="선진(주)", report_no="SJ002", raw_materials="돼지고기", api_source="샘플"),
                FoodItem(food_name="선진 한돈 앞다리살", category="돼지고기", manufacturer="선진(주)", report_no="SJ003", raw_materials="돼지고기", api_source="샘플"),
            ],
            "목우촌(주)": [
                FoodItem(food_name="목우촌 뚝심한우", category="소고기", manufacturer="목우촌(주)", report_no="MW001", raw_materials="한우", api_source="샘플"),
                FoodItem(food_name="목우촌 주부9단 베이컨", category="베이컨", manufacturer="목우촌(주)", report_no="MW002", raw_materials="돼지고기, 소금, 향신료", api_source="샘플"),
                FoodItem(food_name="목우촌 프리미엄 소시지", category="소시지", manufacturer="목우촌(주)", report_no="MW003", raw_materials="돼지고기, 전분, 소금", api_source="샘플"),
            ],
            "도드람푸드(주)": [
                FoodItem(food_name="도드람 한돈 삼겹살", category="돼지고기", manufacturer="도드람푸드(주)", report_no="DD001", raw_materials="돼지고기", api_source="샘플"),
                FoodItem(food_name="도드람 수제 햄", category="햄", manufacturer="도드람푸드(주)", report_no="DD002", raw_materials="돼지고기, 소금, 향신료", api_source="샘플"),
                FoodItem(food_name="도드람 프랑크 소시지", category="소시지", manufacturer="도드람푸드(주)", report_no="DD003", raw_materials="돼지고기, 전분, 소금", api_source="샘플"),
            ],
            "체리부로(주)": [
                FoodItem(food_name="체리부로 닭가슴살", category="닭고기", manufacturer="체리부로(주)", report_no="CB001", raw_materials="닭가슴살", api_source="샘플"),
                FoodItem(food_name="체리부로 훈제치킨", category="닭고기가공품", manufacturer="체리부로(주)", report_no="CB002", raw_materials="닭고기, 소금, 훈연향", api_source="샘플"),
                FoodItem(food_name="체리부로 닭안심", category="닭고기", manufacturer="체리부로(주)", report_no="CB003", raw_materials="닭안심", api_source="샘플"),
            ],
            "사조팜스(주)": [
                FoodItem(food_name="사조팜스 통닭다리", category="닭고기", manufacturer="사조팜스(주)", report_no="SP001", raw_materials="닭다리", api_source="샘플"),
                FoodItem(food_name="사조팜스 닭볶음탕용", category="닭고기", manufacturer="사조팜스(주)", report_no="SP002", raw_materials="닭고기", api_source="샘플"),
                FoodItem(food_name="사조팜스 닭가슴살 슬라이스", category="닭고기", manufacturer="사조팜스(주)", report_no="SP003", raw_materials="닭가슴살", api_source="샘플"),
            ],
        }

        items = sample_products.get(company_name, [])

        # 페이지네이션
        total = len(items)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        return FoodSearchResult(
            total_count=total,
            page=page,
            per_page=per_page,
            items=items[start_idx:end_idx]
        )

    def _get_sample_foods(
        self,
        keyword: str,
        page: int,
        per_page: int
    ) -> FoodSearchResult:
        """샘플 식품 데이터"""
        # 모든 제품 수집
        all_products = []
        for company, products in {
            "농심(주)": self._get_sample_products_by_company("농심(주)", 1, 100).items,
            "삼양식품(주)": self._get_sample_products_by_company("삼양식품(주)", 1, 100).items,
            "오뚜기(주)": self._get_sample_products_by_company("오뚜기(주)", 1, 100).items,
        }.items():
            all_products.extend(products)

        # 키워드 필터
        if keyword:
            filtered = [
                p for p in all_products
                if keyword.lower() in p.food_name.lower()
                or keyword.lower() in (p.category or "").lower()
            ]
        else:
            filtered = all_products

        total = len(filtered)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        return FoodSearchResult(
            total_count=total,
            page=page,
            per_page=per_page,
            items=filtered[start_idx:end_idx]
        )


# 지역 목록 반환
def get_regions():
    return list(REGION_CODES.keys())

def get_business_types():
    return list(BUSINESS_TYPES.keys())


# 싱글톤 인스턴스
food_api_service = FoodAPIService()
