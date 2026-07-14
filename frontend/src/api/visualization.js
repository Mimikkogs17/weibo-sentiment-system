import http from "./http";
export const getVisualizationEvent = (eventId) => http.get(`/visualization/event/${eventId}`);
export const uploadVisualizationCsv = (formData) =>
  http.post("/visualization/upload_csv", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });