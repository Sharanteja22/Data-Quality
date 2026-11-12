import api from "./client";
// export const getBatches = async () => (await api.get("/batches")).data;
// export const getBatch = async id => (await api.get(`/batches/${encodeURIComponent(id)}`)).data;
// export const uploadBatch = async file => { const f = new FormData(); f.append("file", file); return (await api.post("/batches/upload", f, { headers: { "Content-Type": "multipart/form-data" } })).data; };

export const getBatches = async () =>
  (await api.get("/batches")).data;

export const getBatch = async (id) =>
  (await api.get(`/batches/${encodeURIComponent(id)}`)).data;

export const uploadBatch = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return (
    await api.post("/batches/upload", formData)
  ).data;
};

// Submit a corrected CSV as a new processing run.
export const replayBatch = async (batchId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  return (
    await api.post(
      `/batches/${encodeURIComponent(batchId)}/replay`,
      formData
    )
  ).data;
};
