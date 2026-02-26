import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CitizenPortal from './pages/CitizenPortal';
import MunicipalityDashboard from './pages/MunicipalityDashboard';
import Login from './pages/Login';
import './index.css';

const ProtectedRoute = ({ children }) => {
    const isAuth = localStorage.getItem('isAuthenticated') === 'true';
    return isAuth ? children : <Login />;
};

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/citizen" element={<CitizenPortal />} />
                <Route path="/login" element={<Login />} />
                <Route path="/municipality" element={
                    <ProtectedRoute>
                        <MunicipalityDashboard />
                    </ProtectedRoute>
                } />
            </Routes>
        </Router>
    );
}

export default App;
