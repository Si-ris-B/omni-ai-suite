import React from "react";
import { createRoot } from "react-dom/client"; // Import createRoot
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./assets/styles/CustomCalendar.css"

// 1. Get the root element
const container = document.getElementById("root");

// 2. Create a root
const root = createRoot(container);

// 3. Use the new root.render method
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);