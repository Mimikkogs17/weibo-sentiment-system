import http from "./http";

export const listHistory = (params) => http.get("/history", { params });
export const getHistoryDetail = (id) => http.get(`/history/${id}`);
export const exportHistoryExcel = (id) =>
  http.post(`/history/${id}/export/excel`, {}, { responseType: "blob" });
export const exportHistoryPdf = (id) =>
  http.post(`/history/${id}/export/pdf`, {}, { responseType: "blob" });