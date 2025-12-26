import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import api from '../api';

const UserProfile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleDeleteAccount = async () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      try {
        await api.delete('/delete_account');
        logout(); // Clear state and token
        navigate('/signup'); // Redirect to signup
      } catch (error) {
        console.error('Failed to delete account:', error);
        alert('Failed to delete account. Please try again.');
      }
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>User Profile</h2>
        <div className="profile-info">
          <label>Username:</label>
          <span>{user?.username}</span>
        </div>
        <div className="profile-actions">
          <button className="back-btn" onClick={() => navigate('/')}>Back to Chat</button>
          <button className="delete-account-btn" onClick={handleDeleteAccount}>
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
