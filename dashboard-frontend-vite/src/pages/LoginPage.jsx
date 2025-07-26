import React from 'react';
import { API_ENDPOINTS } from '../config';
import './LoginPage.css';

export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = API_ENDPOINTS.AUTH.LOGIN;
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <h2 className="login-title">Login to access the dashboard</h2>
        <button onClick={handleLogin} className="login-button">
          Login with Discord
        </button>
      </div>
    </div>
  );
} 