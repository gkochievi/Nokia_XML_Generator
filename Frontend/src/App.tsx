import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import HomePage from './pages/HomePage';
import ModernizationPage from './pages/ModernizationPage';
import XmlViewerPage from './pages/XmlViewerPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/modernization" element={<ModernizationPage />} />
        <Route path="/xml-viewer" element={<XmlViewerPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
