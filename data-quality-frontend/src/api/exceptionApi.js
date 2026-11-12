import api from "./client";
export const updateException=async(id,payload)=>(await api.patch(`/exceptions/${encodeURIComponent(id)}`,payload)).data;