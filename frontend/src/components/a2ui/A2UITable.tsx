import React, { useState, useMemo } from 'react';
import { Table, Search, ArrowUpDown, Download } from 'lucide-react';
import type { DataTableData as A2UIDataTableData } from '../../types/a2ui';

interface Props {
  data: A2UIDataTableData;
}

export const A2UITable: React.FC<Props> = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const columns = data.columns || [];
  const rows = data.rows || [];

  // Filter rows by search term
  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return rows;
    const lower = searchTerm.toLowerCase();
    return rows.filter((row) =>
      row.some((cell) => cell !== null && String(cell).toLowerCase().includes(lower))
    );
  }, [rows, searchTerm]);

  // Sort rows if column selected
  const sortedRows = useMemo(() => {
    if (sortCol === null) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const valA = a[sortCol] ?? '';
      const valB = b[sortCol] ?? '';
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRows, sortCol, sortAsc]);

  const handleSort = (colIdx: number) => {
    if (sortCol === colIdx) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(colIdx);
      setSortAsc(true);
    }
  };

  const exportCSV = () => {
    const sanitizeCSVCell = (val: any): string => {
      let str = val !== null && val !== undefined ? String(val) : '';
      // Mitigate CSV Formula Injection (DDE) if cell starts with formula characters
      if (/^[=+\-@\t\r]/.test(str)) {
        str = `'${str}`;
      }
      return `"${str.replace(/"/g, '""')}"`;
    };

    const header = columns.map(sanitizeCSVCell).join(',');
    const body = sortedRows.map((r) => r.map(sanitizeCSVCell).join(',')).join('\n');
    const blob = new Blob([`${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${data.title.toLowerCase().replace(/\s+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="a2ui-card a2ui-table-container">
      <div className="a2ui-card-header" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="a2ui-badge-icon">
            <Table size={16} className="text-nypl-red" />
          </div>
          <div>
            <h4 className="a2ui-card-title">{data.title}</h4>
            <p className="a2ui-card-subtitle">{sortedRows.length} record{sortedRows.length === 1 ? '' : 's'}</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {data.searchable !== false && (
            <div className="a2ui-table-search-box">
              <Search size={13} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Filter table..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="a2ui-table-search-input"
              />
            </div>
          )}
          <button
            className="a2ui-btn-secondary"
            onClick={exportCSV}
            title="Download CSV"
            style={{ padding: '5px 9px', fontSize: '12px' }}
          >
            <Download size={13} />
            <span>CSV</span>
          </button>
        </div>
      </div>

      <div className="a2ui-table-wrapper">
        <table className="a2ui-table">
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() => data.sortable !== false && handleSort(idx)}
                  style={{ cursor: data.sortable !== false ? 'pointer' : 'default' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>{col}</span>
                    {data.sortable !== false && <ArrowUpDown size={11} color="var(--text-muted)" />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  No matching records found.
                </td>
              </tr>
            ) : (
              sortedRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx}>
                      {cell !== null && cell !== undefined ? String(cell) : '—'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
