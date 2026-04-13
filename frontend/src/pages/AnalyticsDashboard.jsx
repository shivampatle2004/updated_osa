import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import BIWorkspace from '../components/BIWorkspace';

/**
 * AnalyticsDashboard Component
 * Now uses the shared BIWorkspace component for a unified experience.
 */
const AnalyticsDashboard = ({ onLogout }) => {
    const { fileId: pathFileId } = useParams();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const queryFileId = queryParams.get('fileId');
    const fileId = pathFileId || queryFileId;
    const initialFileName = queryParams.get('fileName') || undefined;
    const navigate = useNavigate();
    const userId = localStorage.getItem('userId');

    const handleGoHome = () => {
        navigate('/dashboard');
    };

    const handleOpenFile = (file) => {
        if (file && file.id) {
            navigate(`/analytics/${file.id}`, { replace: true });
        }
    };

    return (
        <BIWorkspace 
            key={fileId || 'empty'}
            fileId={fileId}
            initialFileName={initialFileName}
            userId={userId}
            onLogout={onLogout}
            onGoHome={handleGoHome}
            onOpenFile={handleOpenFile}
        />
    );
};

export default AnalyticsDashboard;
