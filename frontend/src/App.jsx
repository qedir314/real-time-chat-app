import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import Chat from './components/Chat';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  return user ? children : <Navigate to="/signin" />;
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/signin" element={!user ? <SignIn /> : <Navigate to="/" />} />
      <Route path="/signup" element={!user ? <SignUp /> : <Navigate to="/" />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Chat />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;