import api from "./client";

export const getBatches = async () => (await api.get("/batches")).data;
export const getBatch = async (batchId) => (await api.get(`/batches/${encodeURIComponent(batchId)}`)).data;
export const uploadBatch = async (file) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post("/batches/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000
  })).data;
};
