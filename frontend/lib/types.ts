// Type definitions for TOEFL Speaking Master

export interface Problem {
  problem_id: string;
  reading_text?: string;  // Task1では不要
  lecture_script?: string;  // Task1では不要
  lecture_audio_url?: string;  // Task1では不要
  question: string;
  topic_category?: string;  // Task1では不要
  task_type: string;
  preparation_time?: number;  // Task1では15秒
  speaking_time?: number;  // Task1では45秒
  created_at?: string;
}

export interface ScoringResponse {
  overall_score: number;
  delivery: {
    score: number;
    feedback: string;
  };
  language_use: {
    score: number;
    feedback: string;
  };
  topic_development: {
    score: number;
    feedback: string;
  };
  improvement_tips: string[];
  user_transcript: string;
}

export interface Task1ScoringResponse {
  overall_score: number;
  delivery_feedback: string;
  language_use_feedback: string;
  topic_dev_feedback: string;
  improvement_tips: string[];
  strengths: string[];
  user_transcript: string;
}

export interface ModelAnswerResponse {
  model_answer: string;
  highlighted_phrases: Array<{
    text: string;
    category: string;
    useful_for_writing?: boolean;
    explanation?: string;  // Task1用
  }>;
}

export interface PracticeSessionSummary {
  id: string;
  task_type: string;
  overall_score?: number;
  created_at: string;
  question?: string;
}

export interface SavedPhrase {
  id: string;
  phrase: string;
  context?: string;
  category?: string;
  is_mastered: boolean;
  created_at: string;
}

export interface Task1Question {
  id: string;
  question: string;
  user_transcript?: string | null;
  overall_score?: number | null;
  created_at: string;
}