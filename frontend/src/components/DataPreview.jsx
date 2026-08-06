export default function DataPreview({ data }) {
  if (!data?.length) return <div>No preview data</div>;

  return (
    <table>
      <tbody>
        {data.slice(0, 5).map((row, i) => (
          <tr key={i}>
            {Object.values(row).map((val, j) => (
              <td key={j}>{String(val)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
