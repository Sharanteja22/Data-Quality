import api from "./client";

export const updateException = async (exceptionId, payload) =>
  (await api.patch(`/exceptions/${encodeURIComponent(exceptionId)}`, payload)).data;
