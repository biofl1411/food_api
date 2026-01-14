/**
 * 업체 검색 플랫폼 - 프론트엔드 스크립트
 */

// 상태 관리
const state = {
    keyword: '',
    region: '',
    businessType: '',
    currentPage: 1,
    perPage: 10,
    totalCount: 0,
    isLoading: false
};

// DOM 요소
const elements = {
    keywordInput: document.getElementById('company-keyword'),
    searchBtn: document.getElementById('search-btn'),
    totalCount: document.getElementById('total-count'),
    loading: document.getElementById('loading'),
    resultTbody: document.getElementById('result-tbody'),
    pagination: document.getElementById('pagination'),
    perPageSelect: document.getElementById('per-page-select'),
    modal: document.getElementById('product-modal'),
    modalCompanyName: document.getElementById('modal-company-name'),
    productLoading: document.getElementById('product-loading'),
    productList: document.getElementById('product-list')
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DEBUG] DOMContentLoaded - 초기화 시작');
    console.log('[DEBUG] searchBtn:', elements.searchBtn);
    setupEventListeners();
    console.log('[DEBUG] 이벤트 리스너 등록 완료');
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 검색 버튼
    elements.searchBtn.addEventListener('click', handleSearch);

    // 엔터 키 검색
    elements.keywordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // 페이지당 결과 수 변경
    elements.perPageSelect.addEventListener('change', (e) => {
        state.perPage = parseInt(e.target.value);
        state.currentPage = 1;
        performSearch();
    });

    // 모달 외부 클릭 시 닫기
    elements.modal.addEventListener('click', (e) => {
        if (e.target === elements.modal) closeModal();
    });

    // ESC 키로 모달 닫기
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// 검색 처리
function handleSearch() {
    console.log('[DEBUG] handleSearch 호출됨');
    // 검색 조건 수집
    state.keyword = elements.keywordInput.value.trim();

    // 지역 수집 (체크된 항목들)
    const checkedRegions = document.querySelectorAll('input[name="region"]:checked');
    state.region = Array.from(checkedRegions).map(cb => cb.value).join(',');

    // 업종 수집
    const checkedBusinessType = document.querySelector('input[name="business_type"]:checked');
    state.businessType = checkedBusinessType ? checkedBusinessType.value : '';

    state.currentPage = 1;
    performSearch();
}

// 검색 실행
async function performSearch() {
    console.log('[DEBUG] performSearch 시작');
    console.log('[DEBUG] state:', JSON.stringify(state));
    if (state.isLoading) return;

    state.isLoading = true;
    showLoading();

    try {
        const params = new URLSearchParams({
            keyword: state.keyword,
            region: state.region,
            business_type: state.businessType,
            page: state.currentPage,
            per_page: state.perPage
        });

        console.log('[DEBUG] API 호출:', `/api/companies?${params}`);
        const response = await fetch(`/api/companies?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        state.totalCount = data.total_count;

        displayResults(data);
        updatePagination(data);
        updateTotalCount(data.total_count);

    } catch (error) {
        console.error('검색 오류:', error);
        showError('검색 중 오류가 발생했습니다.');
    } finally {
        state.isLoading = false;
        hideLoading();
    }
}

// 결과 표시
function displayResults(data) {
    const { items } = data;

    if (items.length === 0) {
        elements.resultTbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="6">조회된 데이터가 없습니다.</td>
            </tr>
        `;
        return;
    }

    const startNo = (state.currentPage - 1) * state.perPage;

    const html = items.map((item, index) => `
        <tr>
            <td class="col-no">${startNo + index + 1}</td>
            <td class="col-license">${escapeHtml(item.license_no || '-')}</td>
            <td class="col-name">
                <a class="company-link" onclick="showCompanyProducts('${escapeHtml(item.company_name)}')">
                    ${escapeHtml(item.company_name)}
                </a>
            </td>
            <td class="col-type">${escapeHtml(item.business_type || '-')}</td>
            <td class="col-address">${escapeHtml(item.address || '-')}</td>
            <td class="col-status">
                <span class="${item.status === '운영' ? 'status-active' : 'status-closed'}">
                    ${escapeHtml(item.status || '-')}
                </span>
            </td>
        </tr>
    `).join('');

    elements.resultTbody.innerHTML = html;
}

// 업체 품목 조회
async function showCompanyProducts(companyName) {
    // 모달 열기
    elements.modal.classList.remove('hidden');
    elements.modalCompanyName.textContent = companyName + ' - 품목 목록';
    elements.productLoading.classList.remove('hidden');
    elements.productList.innerHTML = '';

    try {
        const response = await fetch(`/api/companies/${encodeURIComponent(companyName)}/products?per_page=50`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayProducts(data.items);

    } catch (error) {
        console.error('품목 조회 오류:', error);
        elements.productList.innerHTML = `
            <div class="no-products">품목 조회 중 오류가 발생했습니다.</div>
        `;
    } finally {
        elements.productLoading.classList.add('hidden');
    }
}

// 품목 목록 표시
function displayProducts(products) {
    if (products.length === 0) {
        elements.productList.innerHTML = `
            <div class="no-products">등록된 품목이 없습니다.</div>
        `;
        return;
    }

    const html = products.map(product => `
        <div class="product-item">
            <div class="product-name">${escapeHtml(product.food_name)}</div>
            <div class="product-info">
                ${product.category ? `<span>📁 ${escapeHtml(product.category)}</span>` : ''}
                ${product.report_no ? `<span>📋 ${escapeHtml(product.report_no)}</span>` : ''}
                ${product.serving_size ? `<span>📦 ${escapeHtml(product.serving_size)}</span>` : ''}
            </div>
            ${product.raw_materials ? `
                <div class="product-info" style="margin-top: 8px; color: #888;">
                    원재료: ${escapeHtml(product.raw_materials.substring(0, 100))}${product.raw_materials.length > 100 ? '...' : ''}
                </div>
            ` : ''}
        </div>
    `).join('');

    elements.productList.innerHTML = html;
}

// 모달 닫기
function closeModal() {
    elements.modal.classList.add('hidden');
}

// 페이지네이션 업데이트
function updatePagination(data) {
    const totalPages = Math.ceil(data.total_count / state.perPage);

    if (totalPages <= 1) {
        elements.pagination.classList.add('hidden');
        return;
    }

    let html = '';

    // 이전 버튼
    html += `
        <button class="page-btn" onclick="goToPage(${state.currentPage - 1})"
                ${state.currentPage === 1 ? 'disabled' : ''}>
            ◀ 이전
        </button>
    `;

    // 페이지 번호들
    const startPage = Math.max(1, state.currentPage - 2);
    const endPage = Math.min(totalPages, state.currentPage + 2);

    if (startPage > 1) {
        html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span style="padding: 0 5px;">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button class="page-btn ${i === state.currentPage ? 'active' : ''}"
                    onclick="goToPage(${i})">
                ${i}
            </button>
        `;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span style="padding: 0 5px;">...</span>`;
        }
        html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // 다음 버튼
    html += `
        <button class="page-btn" onclick="goToPage(${state.currentPage + 1})"
                ${state.currentPage === totalPages ? 'disabled' : ''}>
            다음 ▶
        </button>
    `;

    elements.pagination.innerHTML = html;
    elements.pagination.classList.remove('hidden');
}

// 페이지 이동
function goToPage(page) {
    state.currentPage = page;
    performSearch();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 총 건수 업데이트
function updateTotalCount(count) {
    elements.totalCount.textContent = count.toLocaleString();
}

// 로딩 표시
function showLoading() {
    elements.loading.classList.remove('hidden');
    elements.resultTbody.innerHTML = '';
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

// 에러 표시
function showError(message) {
    elements.resultTbody.innerHTML = `
        <tr class="empty-row">
            <td colspan="6">${escapeHtml(message)}</td>
        </tr>
    `;
}

// HTML 이스케이프
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
