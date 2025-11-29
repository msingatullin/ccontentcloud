import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { Navigation } from './components/Navigation/Navigation';
import { Dashboard } from './pages/Dashboard';
import { Agents } from './pages/Agents';
import { Content } from './pages/Content';
import { CreateContent } from './pages/CreateContent';
import { News } from './pages/News';
import { Settings } from './pages/Settings';
import { ProjectSettings } from './pages/ProjectSettings';
import LandingPage from './pages/landing/LandingPage';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import VerifyEmail from './components/Auth/VerifyEmail';
import ForgotPassword from './components/Auth/ForgotPassword';
import UserProfile from './components/Auth/UserProfile';
import ProtectedRoute, { PublicRoute } from './components/Auth/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { ProjectProvider } from './contexts/ProjectContext';
import { theme } from './styles/theme';

// Глобальные стили
const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: ${props => props.theme.colors.background};
    color: ${props => props.theme.colors.text};
    line-height: 1.6;
  }

  code {
    font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
      monospace;
  }

  a {
    color: ${props => props.theme.colors.primary};
    text-decoration: none;
    transition: color 0.2s ease;
  }

  a:hover {
    color: ${props => props.theme.colors.primaryHover};
  }

  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    outline: none;
    transition: all 0.2s ease;
  }

  input, textarea, select {
    font-family: inherit;
    outline: none;
  }

  /* Скроллбар */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: ${props => props.theme.colors.background};
  }

  ::-webkit-scrollbar-thumb {
    background: ${props => props.theme.colors.border};
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${props => props.theme.colors.textSecondary};
  }
`;

const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: ${props => props.theme.colors.background};
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 280px; /* Ширина навигации */
  transition: margin-left 0.3s ease;

  @media (max-width: 768px) {
    margin-left: 0;
  }
`;

const ContentArea = styled.div`
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;

  @media (max-width: 768px) {
    padding: 16px;
  }
`;

function App() {
  return (
    <HelmetProvider>
      <ThemeProvider theme={theme}>
        <GlobalStyle />
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              {/* Публичные маршруты */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } />
              <Route path="/register" element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              } />
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              
              {/* Защищенные маршруты */}
              <Route path="/dashboard/*" element={
                <ProtectedRoute>
                  <AppContainer>
                    <Navigation />
                    <MainContent>
                      <ContentArea>
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/agents" element={<Agents />} />
                          <Route path="/content" element={<Content />} />
                          <Route path="/create-content" element={<CreateContent />} />
                          <Route path="/news" element={<News />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="/profile" element={<UserProfile />} />
                        <Route path="/projects/:id/settings" element={<ProjectSettings />} />
                        </Routes>
                      </ContentArea>
                    </MainContent>
                  </AppContainer>
                </ProtectedRoute>
              } />
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}

export default App;
