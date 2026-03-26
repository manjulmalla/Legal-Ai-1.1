// Preferences Routes
const express = require('express');
const router = express.Router();
const verifyToken = require('../middlewares/authMiddleware');
const { getPreferences, savePreferences } = require('../controllers/preferencesController');

// Get user preferences - Protected route
router.get('/', verifyToken, getPreferences);

// Save user preferences - Protected route
router.post('/', verifyToken, savePreferences);

module.exports = router;
