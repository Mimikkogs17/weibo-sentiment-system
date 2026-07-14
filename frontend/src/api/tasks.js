import http from "./http";
export const createTask = (data) => http.post("/tasks/create", data);