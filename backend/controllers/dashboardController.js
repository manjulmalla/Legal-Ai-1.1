const User = require('../models/userModel');
const jwt = require('jsonwebtoken');

// ---------- GET DASHBOARD DATA ----------
const getDashboardData = async (req, res) => {
  try {
    // Get user details from request (passed by middleware)
    const userId = req.user?.id;
    const userRole = req.user?.role;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized - User not found'
      });
    }

    // Fetch user from database
    const user = await User.findById(userId);

    if (!user) {
      return res.status(404).json({
        status: 'error',
        message: 'User not found'
      });
    }

    // Prepare dashboard data based on role
    let dashboardData = {
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role
      },
      isAdmin: userRole === 'admin'
    };

    if (userRole === 'admin') {
      // Admin Dashboard - Get stats and users
      const totalUsers = await User.countDocuments();
      const adminUsers = await User.countDocuments({ role: 'admin' });
      const regularUsers = totalUsers - adminUsers;

      dashboardData.admin = {
        totalUsers: totalUsers,
        adminCount: adminUsers,
        userCount: regularUsers,
        stats: {
          registeredToday: 0,
          activeUsers: regularUsers
        }
      };

      dashboardData.message = 'Admin dashboard data loaded';
    } else {
      // User Dashboard
      dashboardData.user_profile = {
        joinDate: user.createdAt || new Date(),
        status: 'active'
      };

      dashboardData.message = 'User dashboard data loaded';
    }

    res.status(200).json({
      status: 'success',
      data: dashboardData
    });

  } catch (error) {
    console.error('Dashboard error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to fetch dashboard data'
    });
  }
};

// ---------- GET ALL USERS (ADMIN ONLY) ----------
const getAllUsers = async (req, res) => {
  try {
    const userRole = req.user?.role;

    if (userRole !== 'admin') {
      return res.status(403).json({
        status: 'error',
        message: 'Forbidden - Admin access required'
      });
    }

    const users = await User.find().select('name email role');

    res.status(200).json({
      status: 'success',
      users: users
    });

  } catch (error) {
    console.error('Get users error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to fetch users'
    });
  }
};

// ---------- DELETE USER (ADMIN ONLY) ----------
const deleteUser = async (req, res) => {
  try {
    const userRole = req.user?.role;
    const userId = req.params.id;

    if (userRole !== 'admin') {
      return res.status(403).json({
        status: 'error',
        message: 'Forbidden - Admin access required'
      });
    }

    const deletedUser = await User.findByIdAndDelete(userId);

    if (!deletedUser) {
      return res.status(404).json({
        status: 'error',
        message: 'User not found'
      });
    }

    res.status(200).json({
      status: 'success',
      message: 'User deleted successfully'
    });

  } catch (error) {
    console.error('Delete user error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to delete user'
    });
  }
};

// ---------- CREATE USER (ADMIN ONLY) ----------
const createUser = async (req, res) => {
  try {
    const userRole = req.user?.role;
    const { name, email, password, role } = req.body;

    if (userRole !== 'admin') {
      return res.status(403).json({
        status: 'error',
        message: 'Forbidden - Admin access required'
      });
    }

    if (!name || !email || !password) {
      return res.status(400).json({
        status: 'error',
        message: 'Name, email, and password are required'
      });
    }

    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) {
      return res.status(409).json({
        status: 'error',
        message: 'User with this email already exists'
      });
    }

    const bcrypt = require('bcryptjs');
    const hashedPassword = await bcrypt.hash(password, 10);

    const newUser = new User({
      name,
      email: email.toLowerCase(),
      password: hashedPassword,
      role: role || 'user'
    });

    await newUser.save();

    res.status(201).json({
      status: 'success',
      message: 'User created successfully',
      user: {
        id: newUser._id,
        name: newUser.name,
        email: newUser.email,
        role: newUser.role
      }
    });

  } catch (error) {
    console.error('Create user error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to create user'
    });
  }
};

// ---------- UPDATE USER (ADMIN ONLY) ----------
const updateUser = async (req, res) => {
  try {
    const userRole = req.user?.role;
    const userId = req.params.id;
    const { name, email, role, password } = req.body;

    if (userRole !== 'admin') {
      return res.status(403).json({
        status: 'error',
        message: 'Forbidden - Admin access required'
      });
    }

    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({
        status: 'error',
        message: 'User not found'
      });
    }

    // Check if email is already taken by another user
    if (email && email.toLowerCase() !== user.email) {
      const existingUser = await User.findOne({ email: email.toLowerCase() });
      if (existingUser) {
        return res.status(409).json({
          status: 'error',
          message: 'Email already in use by another user'
        });
      }
      user.email = email.toLowerCase();
    }

    if (name) user.name = name;
    if (role) user.role = role;
    
    if (password) {
      const bcrypt = require('bcryptjs');
      user.password = await bcrypt.hash(password, 10);
    }

    await user.save();

    res.status(200).json({
      status: 'success',
      message: 'User updated successfully',
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Update user error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to update user'
    });
  }
};

module.exports = {
  getDashboardData,
  getAllUsers,
  deleteUser,
  createUser,
  updateUser
};
