import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AppProvider } from './contexts/AppContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { PermProvider } from './contexts/PermContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import AlertPage from './pages/AlertPage';
import AlertListPage from './pages/AlertListPage';
import CasePage from './pages/CasePage';
import NotFoundPage from './pages/NotFoundPage';
import AdminLayout from './pages/admin/AdminLayout';
import DatasourcePage from './pages/admin/DatasourcePage';
import MetadataPage from './pages/admin/MetadataPage';
import SkillPage from './pages/admin/SkillPage';
import FewShotPage from './pages/admin/FewShotPage';
import RoleManagement from './pages/admin/RoleManagement';
import UserManagement from './pages/admin/UserManagement';
import BenchmarkPage from './pages/admin/BenchmarkPage';
import ModelManagement from './pages/admin/ModelManagement';
import LogViewer from './pages/admin/LogViewer';

function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <ThemeProvider>
          <AuthProvider>
            <PermProvider>
            <AppProvider>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route element={<AppLayout />}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/alerts/new" element={<AlertPage />} />
                  <Route path="/alerts/list" element={<AlertListPage />} />
                  <Route path="/cases/new" element={<CasePage />} />
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route path="datasources" element={<DatasourcePage />} />
                    <Route path="metadata" element={<MetadataPage />} />
                    <Route path="skills" element={<SkillPage />} />
                    <Route path="few-shot" element={<FewShotPage />} />
                    <Route path="roles" element={<RoleManagement />} />
                    <Route path="users" element={<UserManagement />} />
                    <Route path="benchmark" element={<BenchmarkPage />} />
                    <Route path="models" element={<ModelManagement />} />
                    <Route path="logs" element={<LogViewer />} />
                  </Route>
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </AppProvider>
            </PermProvider>
          </AuthProvider>
        </ThemeProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
