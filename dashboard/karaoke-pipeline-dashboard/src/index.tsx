// src/index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Admin, Resource } from 'react-admin';
import App from './App';
import dataProvider from './dataProvider';
import reportWebVitals from './reportWebVitals';
import './index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Admin dataProvider={dataProvider}>
      {/* Example Resource setup */}
      <Resource name="files" />
      {/* Add your resources here */}
    </Admin>
  </React.StrictMode>
);

reportWebVitals();
