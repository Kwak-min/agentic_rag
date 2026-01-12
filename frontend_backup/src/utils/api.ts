// API 유틸리티 - JWT 토큰 자동 포함

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface RequestOptions extends RequestInit {
  requireAuth?: boolean;
}

/**
 * JWT 토큰이 포함된 API 요청
 */
export async function apiRequest(
  endpoint: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { requireAuth = true, headers = {}, ...restOptions } = options;

  // 기본 헤더 설정
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // 인증이 필요한 경우 JWT 토큰 추가
  if (requireAuth) {
    const token = localStorage.getItem('access_token');
    if (token) {
      (defaultHeaders as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: defaultHeaders,
    });

    // 401 Unauthorized - 토큰 만료 또는 인증 실패
    if (response.status === 401 && requireAuth) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
    }

    return response;
  } catch (error) {
    console.error('API 요청 오류:', error);
    throw error;
  }
}

/**
 * GET 요청
 */
export async function apiGet(endpoint: string, requireAuth = true) {
  const response = await apiRequest(endpoint, {
    method: 'GET',
    requireAuth,
  });
  return response.json();
}

/**
 * POST 요청
 */
export async function apiPost(
  endpoint: string,
  data: any,
  requireAuth = true
) {
  const response = await apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
    requireAuth,
  });
  return response.json();
}

/**
 * PUT 요청
 */
export async function apiPut(
  endpoint: string,
  data: any,
  requireAuth = true
) {
  const response = await apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
    requireAuth,
  });
  return response.json();
}

/**
 * DELETE 요청
 */
export async function apiDelete(endpoint: string, requireAuth = true) {
  const response = await apiRequest(endpoint, {
    method: 'DELETE',
    requireAuth,
  });
  return response.json();
}

// 편의 함수들
export const api = {
  get: apiGet,
  post: apiPost,
  put: apiPut,
  delete: apiDelete,
  request: apiRequest,
};

export default api;
