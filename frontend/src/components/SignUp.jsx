import React, { useState } from 'react';
import api from '../api';
import { Link, useNavigate } from 'react-router-dom';

const SignUp = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (username.length < 3) {
      setError("Username must be at least 3 characters long");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }
    if (!/\d/.test(password)) {
      setError("Password must contain at least one number");
      return;
    }
    try {
      await api.post('/signup', { username, password });
      navigate('/signin');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to sign up');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-form-box">
        <h2>Sign Up</h2>
        {error && <p className="error">{error}</p>}
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Sign Up</button>
        </form>
        <p>
          Already have an account? <Link to="/signin">Sign In</Link>
        </p>
      </div>
    </div>
  );
};

export default SignUp;
