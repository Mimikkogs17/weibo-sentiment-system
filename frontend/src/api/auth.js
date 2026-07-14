import http from "./http";

export const loginApi = (data) => http.post("/auth/login", data);
export const registerApi = (data) => http.post("/auth/register", data);
export const getMeApi = () => http.get("/auth/me");
export const changePasswordApi = (data) => http.post("/auth/change_password", data);