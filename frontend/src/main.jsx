import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
// Optional: Import global CSS if needed, but ChakraProvider handles resets
// import './index.css'

const rootElement = document.getElementById('root');
if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    );
} else {
    console.error("Failed to find the root element. Ensure there's an element with id='root' in your index.html.");
}