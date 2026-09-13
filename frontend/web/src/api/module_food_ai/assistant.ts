import { NO_AUTH_FLAG, request } from "@utils";

export interface AssistantQuestionRequest {
  question: string;
  conversation_id?: string;
}

export interface AssistantServiceRecommendation {
  name: string;
  route: string;
}

export interface AssistantQuestionResult {
  answer: string;
  conversation_id: string;
  recommended_services: AssistantServiceRecommendation[];
  sources: string[];
  disclaimer: "AI 生成，仅供辅助参考";
}

export const AssistantAPI = {
  async ask(body: AssistantQuestionRequest): Promise<AssistantQuestionResult> {
    const response = await request<ApiResponse<AssistantQuestionResult>>({
      url: "/food-ai/assistant/questions",
      method: "post",
      data: body,
      headers: { Authorization: NO_AUTH_FLAG },
      timeout: 30_000,
    });
    return response.data.data;
  },
};
