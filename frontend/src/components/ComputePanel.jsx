import { useState } from "react";
import { computeDataset } from "../api/dataset";

export default function ComputePanel({ datasetId, onDone }) {
  const [feature, setFeature] = useState("");

  const run = async () => {
    await computeDataset(datasetId, { feature });
    onDone?.();
  };

  return (
    <div>
      <input value={feature} onChange={(e) => setFeature(e.target.value)} placeholder="Feature name" />
      <button onClick={run}>Compute</button>
    </div>
  );
}
