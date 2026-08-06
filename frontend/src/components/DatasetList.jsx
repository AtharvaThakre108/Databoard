export default function DatasetList({ datasets = [], onSelect }) {
  return (
    <div>
      {datasets.map((d) => (
        <div key={d._id} onClick={() => onSelect?.(d)}>
          {d.name || d.filename || d._id}
        </div>
      ))}
    </div>
  );
}
