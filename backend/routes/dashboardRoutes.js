const express = require('express');
const router = express.Router();
const { getDashboardData, getAllUsers, deleteUser, createUser, updateUser } = require('../controllers/dashboardController');
const verifyToken = require('../middlewares/authMiddleware');

// All dashboard routes require authentication
router.use(verifyToken);

// Get dashboard data (admin or user based on role)
router.get('/', getDashboardData);

// Admin only - Get all users
router.get('/users', getAllUsers);

// Admin only - Create new user
router.post('/users', createUser);

// Admin only - Update user
router.put('/users/:id', updateUser);

// Admin only - Delete user
router.delete('/users/:id', deleteUser);

module.exports = router;
