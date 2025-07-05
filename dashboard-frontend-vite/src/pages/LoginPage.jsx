import React from 'react';
import './LoginPage.css';

export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = 'http://13.239.95.169:8000/api/auth/login';
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