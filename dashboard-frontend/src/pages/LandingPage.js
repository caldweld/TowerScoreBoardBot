import React from 'react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div style={{ textAlign: 'center', marginTop: '10vh' }}>
      <h1>Welcome to Tower Scoreboard Dashboard</h1>
      <Link to="/login">
        <button style={{ fontSize: '1.2em', padding: '0.5em 2em' }}>
          Login with Discord
        
        </button>
      </Link>
    </div>
  );
} 