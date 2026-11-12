import axios from "axios";
const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||"/api",timeout:120000});
api.interceptors.request.use(config=>{const token=sessionStorage.getItem("dq_access_token");if(token)config.headers.Authorization=`Bearer ${token}`;return config;});
api.interceptors.response.use(r=>r,error=>{if(error.response?.status===401){sessionStorage.removeItem("dq_access_token");sessionStorage.removeItem("dq_user");if(!window.location.pathname.startsWith("/login")&&!window.location.pathname.startsWith("/register"))window.location.href="/login";}return Promise.reject(error);});
export default api;