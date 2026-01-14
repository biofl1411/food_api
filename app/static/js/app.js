/**
 * 식품 영양정보 검색 플랫폼 - 프론트엔드 스크립트
 */

// 상태 관리
const state = {
    currentQuery: '',
    currentPage: 1,
    perPage: 10,
    totalCount: 0,
    isLoading: false
};

// DOM 요소
const elements = {
    searchForm: document.getElementById('search-form'),
    searchInput: document.getElementById('search-input'),
    searchStatus: document.getElementById('search-status'),
    loading: document.getElementById('loading'),
    resultsContainer: document.getElementById('results-container'),
    pagination: document.getElementById('pagination')
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    showInitialState();
    setupEventListeners();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    elements.searchForm.addEventListener('submit', handleSearch);
}

// 검색 처리
async function handleSearch(e) {
    e.preventDefault();

    const query = elements.searchInput.value.trim();
    if (!query) return;

    state.currentQuery = query;
    state.currentPage = 1;

    await performSearch();
}

// 페이지 변경
async function goToPage(page) {
    state.currentPage = page;
    await performSearch();

    // 결과 영역으로 스크롤
    elements.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 검색 실행
async function performSearch() {
    if (state.isLoading) return;

    state.isLoading = true;
    showLoading();
    hideStatus();

    try {
        const params = new URLSearchParams({
            q: state.currentQuery,
            page: state.currentPage,
            per_page: state.perPage
        });

        const response = await fetch(`/api/search?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        state.totalCount = data.total_count;

        displayResults(data);
        updatePagination(data);
        showStatus(data);

    } catch (error) {
        console.error('검색 오류:', error);
        showError('검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
        state.isLoading = false;
        hideLoading();
    }
}

// 결과 표시
function displayResults(data) {
    const { items } = data;

    if (items.length === 0) {
        showNoResults();
        return;
    }

    const html = items.map(item => createFoodCard(item)).join('');
    elements.resultsContainer.innerHTML = html;
}

// 식품 카드 생성
function createFoodCard(food) {
    const formatValue = (value, unit = '') => {
        if (value === null || value === undefined) return '-';
        return `${value}${unit}`;
    };

    return `
        <article class="food-card">
            <div class="food-header">
                <h2 class="food-name">${escapeHtml(food.food_name)}</h2>
                ${food.category ? `<span class="food-category">${escapeHtml(food.category)}</span>` : ''}
            </div>

            <div class="food-meta">
                ${food.serving_size ? `<span>📏 1회 제공량: ${escapeHtml(food.serving_size)}</span>` : ''}
                ${food.manufacturer ? `<span>🏭 제조사: ${escapeHtml(food.manufacturer)}</span>` : ''}
            </div>

            <div class="nutrition-grid">
                <div class="nutrition-item">
                    <div class="nutrition-label">열량</div>
                    <div class="nutrition-value calories">${formatValue(food.calories, 'kcal')}</div>
                </div>
                <div class="nutrition-item">
                    <div class="nutrition-label">탄수화물</div>
                    <div class="nutrition-value carbs">${formatValue(food.carbohydrate, 'g')}</div>
                </div>
                <div class="nutrition-item">
                    <div class="nutrition-label">단백질</div>
                    <div class="nutrition-value protein">${formatValue(food.protein, 'g')}</div>
                </div>
                <div class="nutrition-item">
                    <div class="nutrition-label">지방</div>
                    <div class="nutrition-value fat">${formatValue(food.fat, 'g')}</div>
                </div>
                <div class="nutrition-item">
                    <div class="nutrition-label">당류</div>
                    <div class="nutrition-value">${formatValue(food.sugar, 'g')}</div>
                </div>
                <div class="nutrition-item">
                    <div class="nutrition-label">나트륨</div>
                    <div class="nutrition-value">${formatValue(food.sodium, 'mg')}</div>
                </div>
            </div>
        </article>
    `;
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
            html += `<span class="page-info">...</span>`;
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
            html += `<span class="page-info">...</span>`;
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

// 상태 표시
function showStatus(data) {
    const start = (state.currentPage - 1) * state.perPage + 1;
    const end = Math.min(state.currentPage * state.perPage, data.total_count);

    elements.searchStatus.innerHTML = `
        '<strong>${escapeHtml(state.currentQuery)}</strong>' 검색 결과:
        총 <strong>${data.total_count.toLocaleString()}</strong>건
        (${start}-${end}번째 표시 중)
    `;
    elements.searchStatus.classList.remove('hidden');
}

function hideStatus() {
    elements.searchStatus.classList.add('hidden');
}

// 초기 상태 표시
function showInitialState() {
    elements.resultsContainer.innerHTML = `
        <div class="initial-state">
            <div class="initial-state-icon">🔍</div>
            <h3>식품 영양정보를 검색해보세요</h3>
            <p>식품명을 입력하면 열량, 탄수화물, 단백질, 지방 등 상세 영양정보를 확인할 수 있습니다.</p>
        </div>
    `;
}

// 결과 없음 표시
function showNoResults() {
    elements.resultsContainer.innerHTML = `
        <div class="no-results">
            <div class="no-results-icon">😔</div>
            <h3>검색 결과가 없습니다</h3>
            <p>'${escapeHtml(state.currentQuery)}'에 대한 검색 결과를 찾을 수 없습니다.<br>다른 키워드로 검색해보세요.</p>
        </div>
    `;
    elements.pagination.classList.add('hidden');
}

// 에러 표시
function showError(message) {
    elements.resultsContainer.innerHTML = `
        <div class="no-results">
            <div class="no-results-icon">⚠️</div>
            <h3>오류 발생</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    elements.pagination.classList.add('hidden');
}

// 로딩 표시
function showLoading() {
    elements.loading.classList.remove('hidden');
    elements.resultsContainer.innerHTML = '';
    elements.pagination.classList.add('hidden');
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

// HTML 이스케이프
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
