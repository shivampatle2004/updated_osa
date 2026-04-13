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
  const [localElements, setLocalElements] = useState(reportElements);

  useEffect(() => {
    if (dataset && dataset.columns) {
      const cols = dataset.columns.map(col => col.name);
      setSelectedColumns(cols);
    }
  }, [dataset]);

  useEffect(() => {
    setLocalElements(reportElements);
  }, [reportElements]);

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
      
      for (const el of localElements) {
        let elementData = null;
        
        if (el.cached_data) {
          if (el.cached_data.is_table && el.cached_data.rows) {
            elementData = el.cached_data.rows;
          } else if (Array.isArray(el.cached_data.labels)) {
            elementData = el.cached_data.labels.map((label, idx) => ({
              name: label,
              value: el.cached_data.values ? el.cached_data.values[idx] : 0
            }));
          }
        }
        
        const elementConfig = {
          title: el.title,
          xField: el.x_axis || el.config?.x_axis,
          yField: el.y_axis || el.config?.y_axis,
          chartType: el.type
        };
        
        if (el.type === 'table' && el.config?.columns) {
          elements.push({
            type: 'table',
            config: {
              columns: el.config.columns,
              rows_per_page: rowsPerPage,
              show_header: showHeader
            },
            data: elementData
          });
        } else if (['bar', 'line', 'pie', 'area', 'column'].includes(el.type)) {
          elements.push({
            type: 'chart',
            config: elementConfig,
            data: elementData
          });
        } else if (el.type === 'text') {
          elements.push({
            type: 'text',
            config: {
              content: el.config?.content || ''
            },
            data: null
          });
        }
      }
      
      if (selectedColumns.length > 0 && (!elements.length || !localElements.length)) {
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
      
      if (activeFileId && elements.length > 0 && elements[0].data === null) {
        delete elements[0].data;
      }

      const pdfResponse = await fetch('/api/reports/generate-pdf-direct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      console.log('PDF response status:', pdfResponse.status, 'content-type:', pdfResponse.headers.get('content-type'));

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
      console.log('PDF blob size:', blob.size, 'bytes');
      
      if (blob.size < 500) {
        throw new Error('PDF generated is too small - may be empty or corrupted');
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