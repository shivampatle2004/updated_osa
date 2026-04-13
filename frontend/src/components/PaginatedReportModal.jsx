import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Table, BarChart } from 'lucide-react';
import './PaginatedReportModal.css';

const PaginatedReportModal = ({
  isOpen,
  onClose,
  fileId,
  dataset,
  fileName
}) => {
  if (!isOpen) return null;

  // Validate fileId exists
  const validFileId = fileId || (dataset && dataset.metadata && dataset.metadata.fileId);

  const [reportName, setReportName] = useState(fileName ? `${fileName} Report` : 'Paginated Report');
  const [pageSize, setPageSize] = useState('A4');
  const [orientation, setOrientation] = useState('portrait');
  const [rowsPerPage, setRowsPerPage] = useState(30);
  const [showHeader, setShowHeader] = useState(true);
  const [showFooter, setShowFooter] = useState(true);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [includeSummary, setIncludeSummary] = useState(true);

  useEffect(() => {
    if (dataset && dataset.columns) {
      const cols = dataset.columns.map(col => col.name);
      setSelectedColumns(cols);
    }
  }, [dataset]);

  const toggleColumn = (colName) => {
    setSelectedColumns(prev => 
      prev.includes(colName)
        ? prev.filter(c => c !== colName)
        : [...prev, colName]
    );
  };

  const selectAllColumns = () => {
    if (dataset && dataset.columns) {
      setSelectedColumns(dataset.columns.map(col => col.name));
    }
  };

  const deselectAllColumns = () => {
    setSelectedColumns([]);
  };

  const handleGenerate = async () => {
    const activeFileId = validFileId;
    if (!activeFileId || selectedColumns.length === 0) {
      alert('Please select at least one column');
      return;
    }

    setIsGenerating(true);

    try {
      const createResponse = await fetch('/api/reports/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: reportName,
          page_size: pageSize,
          orientation: orientation,
          elements: [
            {
              type: 'table',
              config_json: {
                data_source_index: 0,
                columns: selectedColumns.map(col => ({ name: col, header: col })),
                rows_per_page: rowsPerPage,
                show_header: showHeader,
                show_footer: showFooter
              }
            }
          ],
          data_sources: [
            {
              connection_id: activeFileId,
              query: null
            }
          ]
        })
      });

      if (!createResponse.ok) {
        const err = await createResponse.json();
        throw new Error(err.detail || 'Failed to create report');
      }

      const createData = await createResponse.json();
      const reportId = createData.id;

      const pdfResponse = await fetch(`/api/reports/${reportId}/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          include_summary: includeSummary
        })
      });

      if (!pdfResponse.ok) {
        const err = await pdfResponse.json();
        throw new Error(err.detail || 'Failed to generate PDF');
      }

      const blob = await pdfResponse.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportName.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      onClose();
    } catch (err) {
      console.error('Error generating report:', err);
      alert('Error: ' + (err.message || 'Failed to generate report. Please try again.'));
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="paginated-report-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="paginated-report-modal">
        <div className="paginated-report-header">
          <h2>
            <FileText size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Paginated Report
          </h2>
          <button className="paginated-report-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="paginated-report-body">
          <div className="paginated-report-section">
            <h3 className="paginated-report-section-title">Report Settings</h3>
            
            <div className="paginated-report-field">
              <label className="paginated-report-label">Report Title</label>
              <input
                type="text"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                className="paginated-report-input"
                placeholder="Enter report title"
              />
            </div>

            <div className="paginated-report-row">
              <div className="paginated-report-field">
                <label className="paginated-report-label">Page Size</label>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(e.target.value)}
                  className="paginated-report-select"
                >
                  <option value="A4">A4</option>
                  <option value="LETTER">Letter</option>
                </select>
              </div>

              <div className="paginated-report-field">
                <label className="paginated-report-label">Orientation</label>
                <select
                  value={orientation}
                  onChange={(e) => setOrientation(e.target.value)}
                  className="paginated-report-select"
                >
                  <option value="portrait">Portrait</option>
                  <option value="landscape">Landscape</option>
                </select>
              </div>
            </div>

            <div className="paginated-report-field">
              <label className="paginated-report-label">Rows per Page</label>
              <input
                type="number"
                value={rowsPerPage}
                onChange={(e) => setRowsPerPage(parseInt(e.target.value) || 30)}
                min={10}
                max={100}
                className="paginated-report-input"
              />
            </div>
          </div>

          <div className="paginated-report-section">
            <h3 className="paginated-report-section-title">Options</h3>
            
            <div className="paginated-report-checkbox-group">
              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={includeSummary}
                  onChange={(e) => setIncludeSummary(e.target.checked)}
                />
                <Table size={16} />
                <span>Include Summary (totals, averages)</span>
              </label>

              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={showHeader}
                  onChange={(e) => setShowHeader(e.target.checked)}
                />
                <span>Show Header on each page</span>
              </label>

              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={showFooter}
                  onChange={(e) => setShowFooter(e.target.checked)}
                />
                <span>Show Footer (Page X of Y)</span>
              </label>
            </div>
          </div>

          <div className="paginated-report-section">
            <h3 className="paginated-report-section-title">Columns to Include</h3>
            
            <div className="paginated-report-column-actions">
              <button onClick={selectAllColumns}>Select All</button>
              <button onClick={deselectAllColumns}>Clear</button>
            </div>
            
            <div className="paginated-report-columns">
              {dataset && dataset.columns ? (
                dataset.columns.map(col => (
                  <label key={col.name} className="paginated-report-column-item">
                    <input
                      type="checkbox"
                      checked={selectedColumns.includes(col.name)}
                      onChange={() => toggleColumn(col.name)}
                    />
                    <span className="column-name">{col.name}</span>
                    <span className="column-type">{col.type}</span>
                  </label>
                ))
              ) : (
                <div style={{ gridColumn: 'span 2', textAlign: 'center', padding: '20px', color: '#64748b' }}>
                  No columns available
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="paginated-report-info">
          {dataset && dataset.metadata && (
            <span>Total Rows: {dataset.metadata.totalRows || dataset.rows?.length || 0}</span>
          )}
          <span>Selected: {selectedColumns.length} columns</span>
        </div>

        <div className="paginated-report-actions">
          <button className="paginated-report-btn paginated-report-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="paginated-report-btn paginated-report-btn-generate" 
            onClick={handleGenerate}
            disabled={isGenerating || selectedColumns.length === 0}
          >
            {isGenerating ? 'Generating...' : (
              <>
                <Download size={16} />
                Generate PDF
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PaginatedReportModal;