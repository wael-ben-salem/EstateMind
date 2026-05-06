import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { PipelineProvider } from './context/PipelineContext';
import { DataProvider } from './context/DataContext';
import AdminDashboard from './pages/AdminDashboard';
import ScraperManagement from './components/ScraperManagement/ScraperManagement';
import DataDashboard from './components/DataDashboard/DataDashboard';
import './styles/theme.js';

function App() {
  return (
    <ConfigProvider>
      <PipelineProvider>
        <DataProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/admin" element={<AdminDashboard />}>
                <Route index element={<ScraperManagement />} />
                <Route path="dashboard" element={<DataDashboard />} />
              </Route>
              <Route path="/" element={<Navigate to="/admin" />} />
            </Routes>
          </BrowserRouter>
        </DataProvider>
      </PipelineProvider>
    </ConfigProvider>
  );
}

export default App;
