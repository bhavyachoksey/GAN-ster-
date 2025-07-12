// API configuration and types aligned with FastAPI backend

const API_BASE_URL = import.meta.env.DEV ? '/api' : 'http://localhost:8000';

// Types that match the backend models
export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
  is_active: boolean;
}

export interface Question {
  id: string;
  title: string;
  description: string;
  tags: string[];
  user_id: string;
  created_at: string;
  answers: string[];
  accepted_answer: string | null;
  answer_count: number;
  username?: string;
}

export interface QuestionCreate {
  title: string;
  description: string;
  tags: string[];
}

export interface Answer {
  id: string;
  question_id: string;
  user_id: string;
  content: string;
  votes: number;
  created_at: string;
  is_accepted: boolean;
  username?: string;
  user_role?: string;
}

export interface AnswerCreate {
  content: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Helper function to make authenticated requests
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// API functions
export const api = {
  // Auth endpoints
  async register(data: RegisterRequest): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }
    return response.json();
  },

  async login(data: LoginRequest): Promise<AuthTokens> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }
    const result = await response.json();
    localStorage.setItem('access_token', result.access_token);
    localStorage.setItem('user', JSON.stringify(result.user));
    return result;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  // Question endpoints
  async getQuestions(skip = 0, limit = 20, tag?: string): Promise<Question[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (tag) params.append('tag', tag);

    const response = await fetch(`${API_BASE_URL}/questions/?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch questions');
    }
    return response.json();
  },

  async getQuestion(id: string): Promise<Question> {
    const response = await fetch(`${API_BASE_URL}/questions/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch question');
    }
    return response.json();
  },

  async createQuestion(data: QuestionCreate): Promise<Question> {
    const response = await fetch(`${API_BASE_URL}/questions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }
    return response.json();
  },

  async deleteQuestion(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/questions/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to delete question');
    }
  },

  // Answer endpoints
  async getAnswers(questionId: string): Promise<Answer[]> {
    const response = await fetch(`${API_BASE_URL}/answers/question/${questionId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch answers');
    }
    return response.json();
  },

  async createAnswer(questionId: string, data: AnswerCreate): Promise<Answer> {
    const response = await fetch(`${API_BASE_URL}/answers/?question_id=${questionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }
    return response.json();
  },

  async generateAIAnswer(questionId: string): Promise<Answer> {
    const response = await fetch(`${API_BASE_URL}/answers/ai-generate?question_id=${questionId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to generate AI answer');
    }
    return response.json();
  },

  async searchQuestions(query: string): Promise<{ results: any[], ai_powered: boolean }> {
    const response = await fetch(`${API_BASE_URL}/questions/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error('Failed to search questions');
    }
    return response.json();
  },

  // Utility functions
  getCurrentUser(): User | null {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
}; 