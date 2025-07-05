import React from 'react';

export default function LandingPage() {
  const handleLogin = () => {
    window.location.href = 'http://13.239.95.169:8000/api/auth/login';
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      fontFamily: 'Arial, sans-serif',
      padding: '10px',
      boxSizing: 'border-box'
    }}>
      <div style={{ 
        maxWidth: '100%', 
        margin: '0 auto', 
        textAlign: 'center',
        paddingTop: '5vh',
        paddingBottom: '20px'
      }}>
        <h1 style={{ 
          fontSize: 'clamp(2rem, 5vw, 3rem)', 
          marginBottom: '15px',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
          lineHeight: '1.2'
        }}>
          Welcome to AUS OFFICIAL Guild
        </h1>
        
        <h2 style={{ 
          fontSize: 'clamp(1.5rem, 4vw, 2rem)', 
          marginBottom: '20px',
          color: '#FFD700',
          textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
        }}>
          (The Tower)
        </h2>

        <div style={{ 
          background: 'rgba(255,255,255,0.1)', 
          borderRadius: '15px',
          padding: '20px',
          marginBottom: '30px',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.2)',
          maxWidth: '90%',
          marginLeft: 'auto',
          marginRight: 'auto'
        }}>
          <h3 style={{ 
            fontSize: 'clamp(1.2rem, 3vw, 1.5rem)', 
            marginBottom: '15px' 
          }}>
            About The Tower
          </h3>
          <p style={{ 
            fontSize: 'clamp(0.9rem, 2.5vw, 1.1rem)', 
            lineHeight: '1.5',
            marginBottom: '15px'
          }}>
            The Tower is an exciting mobile video game where players climb through increasingly challenging levels, 
            battling monsters and collecting powerful upgrades. Each tier presents unique challenges and rewards, 
            making every run an adventure!
          </p>
          <p style={{ 
            fontSize: 'clamp(0.9rem, 2.5vw, 1.1rem)', 
            lineHeight: '1.5',
            marginBottom: '15px'
          }}>
            Join our guild to track your progress, compare stats with fellow players, and climb the leaderboards together. 
            Whether you're a newcomer or a tower veteran, there's always room to grow and improve!
          </p>
        </div>

        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          gap: '15px',
          flexWrap: 'wrap',
          marginBottom: '20px'
        }}>
          <button 
            onClick={handleLogin}
            style={{ 
              fontSize: 'clamp(1rem, 3vw, 1.3rem)', 
              padding: 'clamp(10px, 3vw, 15px) clamp(20px, 5vw, 30px)',
              backgroundColor: '#FFD700',
              color: '#333',
              border: 'none',
              borderRadius: '25px',
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              transition: 'transform 0.2s, box-shadow 0.2s',
              whiteSpace: 'nowrap'
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
        </div>

        <div style={{ 
          fontSize: 'clamp(0.8rem, 2vw, 0.9rem)',
          opacity: '0.8',
          padding: '0 10px'
        }}>
          <p>Track your progress • Compare with guildmates • Climb the leaderboards</p>
        </div>
      </div>
    </div>
  );
} 