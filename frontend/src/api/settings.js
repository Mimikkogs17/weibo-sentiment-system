import http from "./http";
export const getIntegrations = () => http.get("/settings/integrations");
export const switchIntegration = (data) => http.post("/settings/integrations/switch", data);