import api from "../utils/axiosConfig";

export const uploadDataset = (formData) =>
  api.post("/dataset", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getDatasets = (page = 1, limit = 10) =>
  api.get(`/dataset?page=${page}&limit=${limit}`);

export const previewDataset = (id) => api.get(`/dataset/${id}/preview`);
export const computeDataset = (id, payload) => api.post(`/dataset/${id}/compute`, payload);
export const plotDataset = (id, params) => api.get(`/dataset/${id}/plot`, { params });
export const deleteDataset = (id) => api.delete(`/dataset/${id}`);
