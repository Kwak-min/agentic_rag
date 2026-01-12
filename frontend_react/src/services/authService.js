import api from './api';

class AuthService {
  /**
   * 로그인
   */
  async login(username, password) {
    const response = await api.post('/api/auth/login', {
      username,
      password,
    });

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }

    return response.data;
  }

  /**
   * 로그아웃
   */
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }

  /**
   * 현재 사용자 정보
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  }

  /**
   * 로그인 여부 확인
   */
  isLoggedIn() {
    return !!localStorage.getItem('access_token');
  }

  /**
   * 관리자 여부 확인
   */
  isAdmin() {
    const user = this.getCurrentUser();
    return user && user.role === 'admin';
  }
}

export default new AuthService();
