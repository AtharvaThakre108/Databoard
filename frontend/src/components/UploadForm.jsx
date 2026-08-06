import { useState } from "react";
import { uploadDataset } from "../api/dataset";

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    await uploadDataset(formData);
    setFile(null);
    onUploaded?.();
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button type="submit">Upload</button>
    </form>
  );
}
