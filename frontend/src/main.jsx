// File: frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client'; // Use client import for React 18+
import App from './App';
// Optional: If you have global CSS not handled by Chakra, import it here
// import './index.css';

// Find the root element in your index.html
const rootElement = document.getElementById('root');

// Ensure the root element exists before trying to render
if (rootElement) {
    // Create a root instance
    const root = ReactDOM.createRoot(rootElement);
    // Render the App component within StrictMode for development checks
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    );
} else {
    // Log an error if the root element is missing
    console.error("Fatal Error: Root element with id 'root' not found in index.html. React app cannot be mounted.");
}