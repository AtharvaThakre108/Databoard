import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { getDatasets } from "../api/dataset";
import UploadForm from "../components/UploadForm";
import DatasetList from "../components/DatasetList";

export default function Dashboard() {
  const [datasets, setDatasets] = useState([]);

  const load = async () => {
    try {
      const res = await getDatasets();
      setDatasets(res.data);
    } catch {
      toast.error("Failed to load datasets");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Upload dataset</h2>
          <UploadForm onUploaded={load} />
        </section>

        <section className="panel">
          <h2>Your datasets</h2>
          <DatasetList datasets={datasets} />
        </section>
      </div>
    </div>
  );
}
