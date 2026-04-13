import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          marginTop: '10%',
          fontFamily: 'sans-serif'
        }}>
          <h2 style={{ color: '#78176b' }}>Oops! Something went wrong.</h2>
          <p>We encountered an unexpected error while rendering this page.</p>
          <button 
            onClick={() => window.location.href = '/'}
            style={{
              padding: '0.8rem 1.5rem',
              background: '#78176b',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Go Back Home
          </button>
          {process.env.NODE_ENV === 'development' && (
            <div style={{
              marginTop: '2rem',
              padding: '1rem',
              background: '#f8f8f8',
              borderRadius: '8px',
              textAlign: 'left',
              overflowX: 'auto'
            }}>
              <code>{this.state.error?.toString()}</code>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
