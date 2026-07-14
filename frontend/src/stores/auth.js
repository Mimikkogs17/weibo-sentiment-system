import { defineStore } from "pinia";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || "",
  }),
  actions: {
    setToken(t) {
      this.token = t;
      localStorage.setItem("token", t);
    },
    logout() {
      this.token = "";
      this.user = null;
      localStorage.removeItem("token");
    }
  }
});