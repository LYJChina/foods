import { NO_AUTH_FLAG, request } from "@utils";

import type {
  DiagnosisAnswers,
  DiagnosisResult,
  PrecheckCreate,
  PrecheckTask,
} from "@/types/food-ai";

const API_PATH = "/food-ai";

export const FoodAIPortalAPI = {
  async createPrecheck(body: PrecheckCreate): Promise<PrecheckTask> {
    const response = await request<ApiResponse<PrecheckTask>>({
      url: API_PATH + "/prechecks",
      method: "post",
      data: body,
      headers: { Authorization: NO_AUTH_FLAG },
    });
    return response.data.data;
  },

  async getPrecheck(taskId: string): Promise<PrecheckTask> {
    const response = await request<ApiResponse<PrecheckTask>>({
      url: API_PATH + "/prechecks/" + encodeURIComponent(taskId),
      method: "get",
      headers: { Authorization: NO_AUTH_FLAG },
    });
    return response.data.data;
  },

  async createDiagnosis(body: DiagnosisAnswers): Promise<DiagnosisResult> {
    const response = await request<ApiResponse<DiagnosisResult>>({
      url: API_PATH + "/diagnoses",
      method: "post",
      data: body,
      headers: { Authorization: NO_AUTH_FLAG },
    });
    return response.data.data;
  },
};
