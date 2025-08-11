import React from 'react';
import './LandingPage.css';
import { API_ENDPOINTS } from '../config';

export default function LandingPage() {
  const handleLogin = () => {
    window.location.href = API_ENDPOINTS.AUTH.LOGIN;
  };

  return (
    <div className="landing-container">
      <div className="landing-content">
        <h1 className="landing-title">
          Welcome to AUS OFFICIAL Guild
        </h1>
        
        <h2 className="landing-subtitle">
          (The Tower)
        </h2>

        <div className="about-section">
          <h3>About The Tower</h3>
          <p>
            The Tower is an exciting mobile video game where players climb through increasingly challenging levels, 
            battling monsters and collecting powerful upgrades. Each tier presents unique challenges and rewards, 
            making every run an adventure!
          </p>
          <p>
            Join our guild to track your progress, compare stats with fellow players, and climb the leaderboards together. 
            Whether you're a newcomer or a tower veteran, there's always room to grow and improve!
          </p>
        </div>

        <div className="login-section">
          <button 
            onClick={handleLogin}
            className="login-btn"
          >
            Login with Discord
          </button>
        </div>

        <div className="footer-text">
          <p>Track your progress • Compare with guildmates • Climb the leaderboards</p>
        </div>
      </div>
    </div>
  );
} 