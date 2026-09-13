import { NO_AUTH_FLAG, request } from "@utils";
const base = "/food-ai/documents";
export const DocumentAPI = {
  async create(file: File, confirmed: boolean) {
    const data = new FormData();
    data.append("file", file, file.name);
    data.append("confirmed_low_sensitivity", String(confirmed));
    return (
      await request<ApiResponse<any>>({
        url: base,
        method: "post",
        data,
        headers: { Authorization: NO_AUTH_FLAG, "Content-Type": "multipart/form-data" },
      })
    ).data.data;
  },
  async status(id: string) {
    return (
      await request<ApiResponse<any>>({
        url: `${base}/${encodeURIComponent(id)}`,
        method: "get",
        headers: { Authorization: NO_AUTH_FLAG },
      })
    ).data.data;
  },
  async content(id: string) {
    return (
      await request<ApiResponse<any>>({
        url: `${base}/${encodeURIComponent(id)}/content`,
        method: "get",
        headers: { Authorization: NO_AUTH_FLAG },
      })
    ).data.data;
  },
  async question(id: string, question: string) {
    return (
      await request<ApiResponse<any>>({
        url: `${base}/${encodeURIComponent(id)}/questions`,
        method: "post",
        data: { question },
        headers: { Authorization: NO_AUTH_FLAG },
      })
    ).data.data;
  },
  async remove(id: string) {
    return (
      await request<ApiResponse<any>>({
        url: `${base}/${encodeURIComponent(id)}`,
        method: "delete",
        headers: { Authorization: NO_AUTH_FLAG },
      })
    ).data.data;
  },
};
