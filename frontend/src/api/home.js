import http from "./http";

export const getDashboard = () => http.get("/home/dashboard");