import api from "../utils/axiosConfig";

export const uploadDataset = (formData) =>
  api.post("/dataset/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getDatasets = () => api.get("/dataset");
export const getDatasetById = (id) => api.get(`/dataset/${id}`);
export const deleteDataset = (id) => api.delete(`/dataset/${id}`);
export const computeDataset = (id, payload) => api.post(`/dataset/${id}/compute`, payload);
