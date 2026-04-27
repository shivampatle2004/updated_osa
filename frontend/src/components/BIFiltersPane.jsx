import React, { useEffect, useMemo, useState } from 'react';
import { X } from 'lucide-react';

const EMPTY_FILTER = { field: '', operator: 'all', value: '' };

const BIFiltersPane = ({ selectedVisual, schema, onUpdateVisual }) => {
    const fieldOptions = useMemo(
        () => (Array.isArray(schema) ? schema.map((s) => s?.column_name).filter(Boolean) : []),
        [schema]
    );
    const [visualFilters, setVisualFilters] = useState([]);
    const [pageFilters, setPageFilters] = useState([]);
    const [reportFilters, setReportFilters] = useState([]);

    useEffect(() => {
        const opts = selectedVisual?.options || {};
        setVisualFilters(Array.isArray(opts.filters) ? opts.filters : []);
        setPageFilters(Array.isArray(opts.pageFilters) ? opts.pageFilters : []);
        setReportFilters(Array.isArray(opts.reportFilters) ? opts.reportFilters : []);
    }, [selectedVisual?.id]);

    const syncToVisual = (nextVisualFilters, nextPageFilters = pageFilters, nextReportFilters = reportFilters) => {
        if (!selectedVisual?.id || !onUpdateVisual) return;
        onUpdateVisual(selectedVisual.id, {
            options: {
                ...(selectedVisual.options || {}),
                filters: nextVisualFilters,
                pageFilters: nextPageFilters,
                reportFilters: nextReportFilters
            }
        });
    };

    const updateFilterList = (section, nextList) => {
        if (section === 'visual') {
            setVisualFilters(nextList);
            syncToVisual(nextList, pageFilters, reportFilters);
        } else if (section === 'page') {
            setPageFilters(nextList);
            syncToVisual(visualFilters, nextList, reportFilters);
        } else {
            setReportFilters(nextList);
            syncToVisual(visualFilters, pageFilters, nextList);
        }
    };

    const renderFilterSection = (title, section, filters, disabled = false) => (
        <div className="bi-pane-section">
            <div className="bi-section-subtitle">{title}</div>
            <div className="bi-filter-dropzone">
                {filters.length === 0 && (
                    <span className="bi-dropzone-empty">{disabled ? 'Select a visual to add filters' : 'No filters applied'}</span>
                )}

                {filters.map((f, idx) => (
                    <div key={`${section}-${idx}`} className="bi-filter-editor-row">
                        <div className="bi-filter-main-grid">
                            <select
                                className="bi-filter-select"
                                value={f.field || ''}
                                disabled={disabled}
                                onChange={(e) => {
                                    const next = [...filters];
                                    next[idx] = { ...next[idx], field: e.target.value };
                                    updateFilterList(section, next);
                                }}
                            >
                                <option value="">Field</option>
                                {fieldOptions.map((field) => (
                                    <option key={field} value={field}>{field}</option>
                                ))}
                            </select>
                            <select
                                className="bi-filter-select"
                                value={f.operator || 'all'}
                                disabled={disabled}
                                onChange={(e) => {
                                    const next = [...filters];
                                    next[idx] = { ...next[idx], operator: e.target.value };
                                    updateFilterList(section, next);
                                }}
                            >
                                <option value="all">All</option>
                                <option value="equals">Equals</option>
                                <option value="contains">Contains</option>
                                <option value="gt">Greater than</option>
                                <option value="lt">Less than</option>
                            </select>
                            <input
                                className="bi-filter-input"
                                type="text"
                                value={f.value ?? ''}
                                disabled={disabled || f.operator === 'all'}
                                placeholder="Value"
                                onChange={(e) => {
                                    const next = [...filters];
                                    next[idx] = { ...next[idx], value: e.target.value };
                                    updateFilterList(section, next);
                                }}
                            />
                            <button
                                type="button"
                                className="bi-filter-remove-btn"
                                disabled={disabled}
                                onClick={() => updateFilterList(section, filters.filter((_, i) => i !== idx))}
                                title="Remove filter"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </div>
                ))}
                <button
                    type="button"
                    className="bi-filter-add-btn"
                    disabled={disabled}
                    onClick={() => updateFilterList(section, [...filters, { ...EMPTY_FILTER }])}
                >
                    Add filter
                </button>
            </div>
        </div>
    );

    return (
        <div className="bi-pane-view">
            <div className="bi-pane-header">
                <span className="bi-pane-title">Filters</span>
            </div>

            <div className="bi-pane-scroll">
                {renderFilterSection('Filters on this visual', 'visual', visualFilters, !selectedVisual)}
                {renderFilterSection('Filters on this page', 'page', pageFilters, !selectedVisual)}
                {renderFilterSection('Filters on all pages', 'report', reportFilters, !selectedVisual)}
            </div>
        </div>
    );
};

export default BIFiltersPane;
