import React from 'react';

export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = 'http://13.239.95.169:8000/api/auth/login';
  };

  return (
    <div style={{ textAlign: 'center', marginTop: '10vh' }}>
      <h2>Login to access the dashboard</h2>
    
      <button onClick={handleLogin} style={{ fontSize: '1.2em', padding: '0.5em 2em' }}>
        Login with Discord
      </button>
    </div>
  );
} 