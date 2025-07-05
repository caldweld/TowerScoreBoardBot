import React from 'react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      fontFamily: 'Arial, sans-serif',
      padding: '20px'
    }}>
      <div style={{ 
        maxWidth: '800px', 
        margin: '0 auto', 
        textAlign: 'center',
        paddingTop: '10vh'
      }}>
        <h1 style={{ 
          fontSize: '3rem', 
          marginBottom: '20px',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          Welcome to AUS OFFICIAL Guild
        </h1>
        
        <h2 style={{ 
          fontSize: '2rem', 
          marginBottom: '30px',
          color: '#FFD700',
          textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
        }}>
          (The Tower)
        </h2>

        <div style={{ 
          background: 'rgba(255,255,255,0.1)', 
          borderRadius: '15px',
          padding: '30px',
          marginBottom: '40px',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          <h3 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>
            About The Tower
          </h3>
          <p style={{ 
            fontSize: '1.1rem', 
            lineHeight: '1.6',
            marginBottom: '20px'
          }}>
            The Tower is an exciting mobile video game where players climb through increasingly challenging levels, 
            battling monsters and collecting powerful upgrades. Each tier presents unique challenges and rewards, 
            making every run an adventure!
          </p>
          <p style={{ 
            fontSize: '1.1rem', 
            lineHeight: '1.6',
            marginBottom: '20px'
          }}>
            Join our guild to track your progress, compare stats with fellow players, and climb the leaderboards together. 
            Whether you're a newcomer or a tower veteran, there's always room to grow and improve!
          </p>
        </div>

        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          gap: '20px',
          flexWrap: 'wrap'
        }}>
          <Link to="/login" style={{ textDecoration: 'none' }}>
            <button style={{ 
              fontSize: '1.3rem', 
              padding: '15px 30px',
              backgroundColor: '#FFD700',
              color: '#333',
              border: 'none',
              borderRadius: '25px',
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              transition: 'transform 0.2s, box-shadow 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
            }}>
              Login with Discord
            </button>
          </Link>
        </div>

        <div style={{ 
          marginTop: '40px',
          fontSize: '0.9rem',
          opacity: '0.8'
        }}>
          <p>Track your progress • Compare with guildmates • Climb the leaderboards</p>
        </div>
      </div>
    </div>
  );
} 