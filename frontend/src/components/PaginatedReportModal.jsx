import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Table, BarChart, Trash2, GripVertical } from 'lucide-react';
import './PaginatedReportModal.css';

const PaginatedReportModal = ({
  isOpen,
  onClose,
  fileId,
  dataset,
  fileName,
  reportElements = [],
  onReportElementsChange
}) => {
  if (!isOpen) return null;

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
  const [includeTableData, setIncludeTableData] = useState(true);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [localElements, setLocalElements] = useState(() => {
    return Array.isArray(reportElements) ? reportElements : [];
  });

  useEffect(() => {
    if (dataset && dataset.columns) {
      const cols = dataset.columns.map(col => col.name);
      setSelectedColumns(cols);
    }
  }, [dataset]);

  useEffect(() => {
    console.log('Report elements updated:', reportElements?.length);
    if (Array.isArray(reportElements) && reportElements.length > 0) {
      setLocalElements(reportElements);
    }
  }, [reportElements]);
  
  useEffect(() => {
    console.log('Modal opened, localElements:', localElements?.length, reportElements?.length);
    if (Array.isArray(reportElements)) {
      setLocalElements(reportElements);
    }
  }, [isOpen]);

  const removeElement = (elementId) => {
    setLocalElements(prev => prev.filter(e => e.id !== elementId));
    if (onReportElementsChange) {
      const updated = localElements.filter(e => e.id !== elementId);
      onReportElementsChange(updated);
    }
  };

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
    setIsGenerating(true);

    try {
      const elements = [];
      const sourceElements = Array.isArray(reportElements) && reportElements.length > 0 ? reportElements : localElements;
      
      console.log('Elements:', sourceElements?.length, 'includeCharts:', includeCharts);
      
      // Add charts
      for (const el of sourceElements) {
        if (['bar', 'line', 'pie', 'area', 'column'].includes(el.type)) {
          elements.push({
            type: 'chart',
            config: {
              title: el.title || el.type,
              xField: el.x_axis,
              yField: el.y_axis,
              chartType: el.type,
              chart_type: el.type
            },
            data: null
          });
        } else if (el.type === 'text') {
          elements.push({
            type: 'text',
            config: { content: el.config?.content || '' },
            data: null
          });
        }
      }
      
      // Add table from selected columns
      if (includeTableData && selectedColumns.length > 0) {
        elements.push({
          type: 'table',
          config: {
            columns: selectedColumns.map(col => ({ name: col, header: col })),
            rows_per_page: rowsPerPage,
            show_header: showHeader
          },
          data: null
        });
      }
      
      if (elements.length === 0 && selectedColumns.length === 0) {
        alert('Please add visualizations to the report or select columns');
        setIsGenerating(false);
        return;
      }
      
      const requestBody = {
        title: reportName,
        page_size: pageSize,
        orientation: orientation,
        elements: elements,
        file_id: activeFileId
      };

      const pdfResponse = await fetch('/api/reports/generate-pdf-direct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      console.log('PDF response:', pdfResponse.status);

      if (pdfResponse.headers.get("content-type") !== "application/pdf") {
        const error = await pdfResponse.json();
        alert("PDF generation failed: " + (error.error || error.detail || 'Unknown error'));
        setIsGenerating(false);
        return;
      }

      if (!pdfResponse.ok) {
        const err = await pdfResponse.json();
        throw new Error(err.detail || 'Failed to generate PDF');
      }

      const blob = await pdfResponse.blob();
      console.log('PDF size:', blob.size, 'bytes');
      
      if (blob.size < 500) {
        throw new Error('PDF too small');
      }
      
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
      console.error('Error:', err);
      alert('Error: ' + (err.message || 'Failed'));
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
              <select
                value={rowsPerPage}
                onChange={(e) => setRowsPerPage(parseInt(e.target.value))}
                className="paginated-report-select"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
                <option value={40}>40</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          {localElements.length > 0 && (
            <div className="paginated-report-section">
              <h3 className="paginated-report-section-title">Added Visualizations</h3>
              <div className="paginated-report-elements-list">
                {localElements.map((el, idx) => (
                  <div key={el.id} className="paginated-report-element-item">
                    <GripVertical size={14} style={{ color: '#9ca3af', marginRight: '8px' }} />
                    <span className="element-type">{el.type}</span>
                    <span className="element-title">{el.title}</span>
                    <button 
                      className="element-remove-btn" 
                      onClick={() => removeElement(el.id)}
                      title="Remove from report"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: '12px', color: '#64748b', marginTop: '8px' }}>
                Added visualizations will be included in the PDF report
              </p>
            </div>
          )}

          <div className="paginated-report-section">
            <h3 className="paginated-report-section-title">Include in Report</h3>
            
            <div className="paginated-report-checkbox-group">
              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={includeCharts}
                  onChange={(e) => setIncludeCharts(e.target.checked)}
                />
                <BarChart size={16} />
                <span>Charts</span>
              </label>

              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={includeTableData}
                  onChange={(e) => setIncludeTableData(e.target.checked)}
                />
                <Table size={16} />
                <span>Table Data</span>
              </label>

              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={includeSummary}
                  onChange={(e) => setIncludeSummary(e.target.checked)}
                />
                <span>Summary (KPIs)</span>
              </label>
            </div>
          </div>

          <div className="paginated-report-section">
            <h3 className="paginated-report-section-title">Page Settings</h3>
            
            <div className="paginated-report-checkbox-group">
              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={showHeader}
                  onChange={(e) => setShowHeader(e.target.checked)}
                />
                <span>Repeat Header</span>
              </label>

              <label className="paginated-report-checkbox">
                <input
                  type="checkbox"
                  checked={showFooter}
                  onChange={(e) => setShowFooter(e.target.checked)}
                />
                <span>Page Numbers</span>
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
            disabled={isGenerating || (selectedColumns.length === 0 && localElements.length === 0)}
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